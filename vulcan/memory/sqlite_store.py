"""SQLite Metadata repository implementation for index cataloging, relationships and Life Logs."""

import sqlite3
import time
from typing import Any


class SQLiteRepository:
    """A direct standard sqlite3 implementation with lightweight migrations."""

    def __init__(self, db_path: str, timeout_seconds: int = 5):
        self.db_path = db_path
        self.timeout_seconds = timeout_seconds
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=self.timeout_seconds)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self) -> None:
        """Initializes tables using light-weight embedded DDL."""
        with self._get_connection() as conn:
            # 1. Metadata catalog mapping Markdown and Vectors
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_catalog (
                    uuid TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    vault_path TEXT NOT NULL,
                    vector_id TEXT,
                    importance TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    version INTEGER DEFAULT 1,
                    source TEXT,
                    correlation_id TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    metadata TEXT
                )
                """)

            # 2. Relationship Graph
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_relationships (
                    source_uuid TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    target_uuid TEXT NOT NULL,
                    PRIMARY KEY (source_uuid, relationship, target_uuid),
                    FOREIGN KEY (source_uuid) REFERENCES memory_catalog (uuid) ON DELETE CASCADE
                )
                """)

            # 3. Life Log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS life_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    subsystem TEXT NOT NULL,
                    action TEXT NOT NULL,
                    result TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    correlation_id TEXT,
                    metadata TEXT
                )
                """)

            # 4. Pending Extractions (Offline LLM Queue)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_extractions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
                """)

            # 5. Conversations & Turns (Staging areas)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    active_model TEXT NOT NULL
                )
                """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES conversations (session_id) ON DELETE CASCADE
                )
                """)
            conn.commit()

    # Catalog Ops
    def delete_catalog(self, uuid: str) -> None:
        """Physically deletes catalog and associated relationships."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM memory_catalog WHERE uuid = ?", (uuid,))
            conn.execute("DELETE FROM memory_relationships WHERE source_uuid = ? OR target_uuid = ?", (uuid, uuid))
            conn.commit()

    def store_catalog(self, record: dict[str, Any]) -> None:
        """Stores or updates a catalog row."""
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memory_catalog (
                    uuid, memory_type, category, title, vault_path, vector_id,
                    importance, confidence, version, source, correlation_id,
                    created_at, updated_at, metadata
                ) VALUES (
                    :uuid, :memory_type, :category, :title, :vault_path, :vector_id,
                    :importance, :confidence, :version, :source, :correlation_id,
                    COALESCE((SELECT created_at FROM memory_catalog WHERE uuid = :uuid), :created_at),
                    :updated_at, :metadata
                ) ON CONFLICT(uuid) DO UPDATE SET
                    memory_type=excluded.memory_type,
                    category=excluded.category,
                    title=excluded.title,
                    vault_path=excluded.vault_path,
                    vector_id=excluded.vector_id,
                    importance=excluded.importance,
                    confidence=excluded.confidence,
                    version=excluded.version,
                    source=excluded.source,
                    correlation_id=excluded.correlation_id,
                    updated_at=excluded.updated_at,
                    metadata=excluded.metadata
                """,
                {
                    "uuid": record["uuid"],
                    "memory_type": record["memory_type"],
                    "category": record["category"],
                    "title": record.get("title", ""),
                    "vault_path": record["vault_path"],
                    "vector_id": record.get("vector_id"),
                    "importance": record["importance"],
                    "confidence": record["confidence"],
                    "version": record.get("version", 1),
                    "source": record.get("source"),
                    "correlation_id": record.get("correlation_id"),
                    "created_at": record.get("created_at", now),
                    "updated_at": now,
                    "metadata": record.get("metadata", "{}"),
                },
            )
            conn.commit()

    def get_catalog(self, uuid: str) -> dict[str, Any] | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM memory_catalog WHERE uuid = ?", (uuid,)).fetchone()
            return dict(row) if row else None

    def list_catalog(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM memory_catalog"
        params: list[Any] = []
        if filters:
            where_clauses = []
            for k, v in filters.items():
                where_clauses.append(f"{k} = ?")
                params.append(v)
            query += " WHERE " + " AND ".join(where_clauses)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    # Relationships
    def add_relationship(self, source_uuid: str, relationship: str, target_uuid: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO memory_relationships (source_uuid, relationship, target_uuid)
                VALUES (?, ?, ?)
                """,
                (source_uuid, relationship, target_uuid),
            )
            conn.commit()

    def get_relationships(self, source_uuid: str) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_relationships WHERE source_uuid = ?", (source_uuid,)
            ).fetchall()
            return [dict(r) for r in rows]

    # Life Log
    def write_life_log(
        self,
        subsystem: str,
        action: str,
        result: str,
        summary: str,
        correlation_id: str | None = None,
        metadata: str = "{}",
    ) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO life_log (timestamp, subsystem, action, result, summary, correlation_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (time.time(), subsystem, action, result, summary, correlation_id, metadata),
            )
            conn.commit()

    def get_life_log(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM life_log ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # Pending Extractions (Offline LLM Queue)
    def queue_extraction(self, session_id: str, user_input: str, assistant_response: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO pending_extractions (session_id, user_input, assistant_response, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, user_input, assistant_response, time.time()),
            )
            conn.commit()

    def get_pending_extractions(self) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM pending_extractions ORDER BY timestamp ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def remove_pending_extraction(self, record_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM pending_extractions WHERE id = ?", (record_id,))
            conn.commit()

    # Staging Conversation & Turns
    def store_conversation(self, session_id: str, active_model: str) -> None:
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (session_id, created_at, updated_at, active_model)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    active_model = excluded.active_model
                """,
                (session_id, now, now, active_model),
            )
            conn.commit()

    def add_turn(self, session_id: str, user_msg: str, assistant_msg: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversation_turns (session_id, user_message, assistant_message, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, user_msg, assistant_msg, time.time()),
            )
            # Update updated_at of conversation
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE session_id = ?",
                (time.time(), session_id),
            )
            conn.commit()

    def get_turns(self, session_id: str) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM conversation_turns WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def clear_turns(self, session_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM conversation_turns WHERE session_id = ?", (session_id,))
            conn.commit()
