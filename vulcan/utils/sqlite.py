"""Direct sqlite3 database manager and migration utilities."""

import os
import sqlite3

from vulcan.config import SQLiteConfig
from vulcan.utils.logging import get_logger


class SQLiteConnectionManager:
    """Manages SQLite connection establishment, transactions, and settings."""

    def __init__(self, config: SQLiteConfig):
        self.db_path = config.db_path
        self.timeout = config.timeout_seconds
        self.logger = get_logger("sqlite")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured sqlite3.Connection with dictionary-based Row mapping."""
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


class SQLiteMigrationRunner:
    """A lightweight, version-based migration runner."""

    def __init__(self, manager: SQLiteConnectionManager):
        self.manager = manager
        self.logger = get_logger("sqlite_migration")

    def initialize_migrations_table(self, conn: sqlite3.Connection) -> None:
        """Ensures the migrations tracking table exists in the target DB."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

    def get_current_version(self, conn: sqlite3.Connection) -> int:
        """Retrieves currently applied migration version integer."""
        self.initialize_migrations_table(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_version;")
        row = cursor.fetchone()
        if row and row[0] is not None:
            val: int = row[0]
            return val
        return 0

    def run_migrations(self, migrations: list[tuple[int, str]]) -> None:
        """Sequentially applies sorted migrations in transaction-safe manner."""
        conn = self.manager.get_connection()
        try:
            current_version = self.get_current_version(conn)
            for version, sql_query in sorted(migrations):
                if version > current_version:
                    try:
                        conn.execute("BEGIN TRANSACTION;")
                        conn.executescript(sql_query)
                        conn.execute("INSERT INTO schema_version (version) VALUES (?);", (version,))
                        conn.commit()
                    except Exception as ex:
                        conn.rollback()
                        raise ex
        finally:
            conn.close()
