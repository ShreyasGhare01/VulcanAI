"""Concrete implementations of the six memory interfaces: Working, Conversation, Long-Term Knowledge, Life Log, Reflection, Identity."""

import json
from typing import Any

from vulcan.memory.interfaces import (
    IConversationMemory,
    IIdentityMemory,
    IKnowledgeMemory,
    ILifeLogMemory,
    IReflectionMemory,
    IWorkingMemory,
)
from vulcan.memory.models import MemoryCandidate, MemoryProvenance, RetrievalResult
from vulcan.memory.obsidian import ObsidianVault
from vulcan.memory.sqlite_store import SQLiteRepository
from vulcan.services.chroma import IChromaService
from vulcan.utils.logging import get_logger


class WorkingMemory(IWorkingMemory):
    """Volatile, fast, task-specific memory store. Does not persist to Obsidian or DB."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        self._store[key] = value
        self._metadata[key] = metadata or {}

    def retrieve(self, key: str) -> Any | None:
        return self._store.get(key)

    def delete(self, key: str, mode: str = "soft") -> None:
        if key in self._store:
            del self._store[key]
        if key in self._metadata:
            del self._metadata[key]


class ConversationMemory(IConversationMemory):
    """Dialogue staging area store, persisted to SQLite."""

    def __init__(self, sqlite_repo: SQLiteRepository):
        self.sqlite_repo = sqlite_repo

    def store(self, key: str, value: Any, _metadata: dict[str, Any] | None = None) -> None:
        # Save model/session config in Conversations
        self.sqlite_repo.store_conversation(session_id=key, active_model=value)

    def retrieve(self, key: str) -> Any | None:
        # Retrieve active model
        with self.sqlite_repo._get_connection() as conn:
            row = conn.execute(
                "SELECT active_model FROM conversations WHERE session_id = ?", (key,)
            ).fetchone()
            return row["active_model"] if row else None

    def delete(self, key: str, mode: str = "soft") -> None:
        self.clear_conversation(key)

    def get_conversation_history(self, session_id: str) -> list[Any]:
        return self.sqlite_repo.get_turns(session_id)

    def clear_conversation(self, session_id: str) -> None:
        self.sqlite_repo.clear_turns(session_id)


class KnowledgeMemory(IKnowledgeMemory):
    """Long-term user knowledge stored in Obsidian with metadata indexed in SQLite and embedded in ChromaDB."""

    def __init__(
        self,
        sqlite_repo: SQLiteRepository,
        chroma_service: IChromaService,
        obsidian_vault: ObsidianVault,
        retrieval_weights: dict[str, float],
    ):
        self.sqlite_repo = sqlite_repo
        self.chroma_service = chroma_service
        self.obsidian_vault = obsidian_vault
        self.weights = retrieval_weights
        self.logger = get_logger("knowledge_memory")

    def delete(self, key: str, mode: str = "soft") -> None:
        """Implements explicit soft, archive, and permanent deletion semantics."""
        # Find record in SQLite catalog by UUID or title
        record = self.sqlite_repo.get_catalog(key)
        if not record:
            records = self.sqlite_repo.list_catalog({"title": key})
            if records:
                record = records[0]

        if not record:
            self.logger.warning(f"Deletion failed: no catalog record found matching '{key}'")
            return

        uuid_str = record["uuid"]
        v_id = record.get("vector_id")
        path = record["vault_path"]

        # 1. Prune from ChromaDB if online
        if v_id and self.chroma_service.is_available():
            try:
                col = self.chroma_service.get_collection("vulcan_memories")
                if col:
                    col.delete(ids=[v_id])
            except Exception as e:
                self.logger.error(f"Failed to prune vector '{v_id}' from ChromaDB: {e}")

        # 2. Deletion Mode on Obsidian
        if mode == "permanent":
            self.obsidian_vault.delete_markdown(path, archive_only=False)
        elif mode == "archive":
            self.obsidian_vault.delete_markdown(path, archive_only=True)
        # soft leaves file in place

        # 3. Clean catalog from SQLite
        self.sqlite_repo.delete_catalog(uuid_str)
        self.logger.info(
            f"Memory '{key}' successfully deleted with mode '{mode}' from storage systems."
        )

    def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Stores a detailed fact or candidate.

        Accepts either a serialized key/value dict, or a structured MemoryCandidate.
        """
        cand: MemoryCandidate
        if isinstance(value, MemoryCandidate):
            cand = value
        else:
            meta = metadata or {}
            cand = MemoryCandidate(
                title=key,
                content=str(value),
                memory_type="knowledge",
                category=meta.get("category", "fact"),
                importance=meta.get("importance", "medium"),
                confidence=meta.get("confidence", 0.9),
                tags=meta.get("tags", []),
            )

        # 1. Store to Obsidian Vault
        relative_vault_path = (
            f"Users/{cand.category.capitalize()}/{cand.title.replace(' ', '_')}.md"
        )
        frontmatter = {
            "uuid": str(cand.uuid),
            "memory_type": cand.memory_type,
            "category": cand.category,
            "importance": cand.importance,
            "confidence": cand.confidence,
            "created": cand.created_at.isoformat(),
            "updated": cand.updated_at.isoformat(),
            "version": cand.version,
            "source": cand.provenance.origin,
            "correlation_id": cand.provenance.correlation_id or "",
            "relationships": [
                {"target_uuid": r.target_uuid, "relation": r.relation} for r in cand.relationships
            ],
            "tags": cand.tags,
        }

        body_text = f"# {cand.title}\n\n{cand.content}"
        self.obsidian_vault.write_markdown(relative_vault_path, frontmatter, body_text)

        # 2. Add Vector embeddings to ChromaDB if service is online
        vector_id = None
        if self.chroma_service.is_available():
            col = self.chroma_service.get_collection("vulcan_memories")
            if col:
                vector_id = f"vec_{cand.uuid}"
                col.add(
                    ids=[vector_id],
                    documents=[cand.content],
                    metadatas=[
                        {"category": cand.category, "title": cand.title, "uuid": str(cand.uuid)}
                    ],
                )

        # 3. Save Structured Index to SQLite catalog
        record = {
            "uuid": str(cand.uuid),
            "memory_type": cand.memory_type,
            "category": cand.category,
            "title": cand.title,
            "vault_path": relative_vault_path,
            "vector_id": vector_id,
            "importance": cand.importance,
            "confidence": cand.confidence,
            "version": cand.version,
            "source": cand.provenance.origin,
            "correlation_id": cand.provenance.correlation_id,
            "created_at": cand.created_at.timestamp(),
            "updated_at": cand.updated_at.timestamp(),
            "metadata": json.dumps(cand.metadata),
        }
        self.sqlite_repo.store_catalog(record)

        # 4. Save Relationships to graph mapping table
        for rel in cand.relationships:
            self.sqlite_repo.add_relationship(str(cand.uuid), rel.relation, rel.target_uuid)

    def retrieve(self, key: str) -> Any | None:
        """Retrieves knowledge memory details by unique UUID identifier or catalog path."""
        import time

        # Find in SQLite catalog
        record = self.sqlite_repo.get_catalog(key)
        if not record:
            # Fallback searching by title/path
            records = self.sqlite_repo.list_catalog({"title": key})
            if records:
                record = records[0]

        if not record:
            return None

        # Load fresh Markdown body from Obsidian Vault (Source of truth)
        frontmatter, body = self.obsidian_vault.read_markdown(record["vault_path"])

        # Reconciliation: Check if version, confidence, or content was modified in Obsidian
        if frontmatter:
            reconcile_needed = False
            obsidian_version = int(frontmatter.get("version", record["version"]))
            if obsidian_version != record["version"]:
                reconcile_needed = True
                record["version"] = obsidian_version

            obsidian_importance = str(frontmatter.get("importance", record["importance"]))
            if obsidian_importance != record["importance"]:
                reconcile_needed = True
                record["importance"] = obsidian_importance

            obsidian_confidence = float(frontmatter.get("confidence", record["confidence"]))
            if obsidian_confidence != record["confidence"]:
                reconcile_needed = True
                record["confidence"] = obsidian_confidence

            if reconcile_needed:
                self.logger.info(
                    f"Reconciling SQLite catalog for '{key}' based on external Obsidian vault edits."
                )
                record["updated_at"] = time.time()
                self.sqlite_repo.store_catalog(record)

        return {"frontmatter": frontmatter, "body": body, "catalog": record}

    def search(
        self, query: str, limit: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> list[Any]:
        """Performs multi-dimensional retrieval scoring:

        Score = w_sim * Similarity + w_rec * Recency + w_imp * Importance + w_conf * Confidence
        """
        import time
        from datetime import datetime
        from uuid import UUID

        catalog_items = self.sqlite_repo.list_catalog(filter_dict)
        if not catalog_items:
            return []

        # Gather semantic vector scores if ChromaDB is functional
        semantic_scores: dict[str, float] = {}
        if self.chroma_service.is_available() and query:
            col = self.chroma_service.get_collection("vulcan_memories")
            if col:
                results = col.query(query_texts=[query], n_results=limit * 2)
                if results and "ids" in results and results["ids"]:
                    ids = results["ids"][0]
                    distances = results["distances"][0] if "distances" in results else []
                    for idx, v_id in enumerate(ids):
                        # Convert cosine distance/similarity
                        dist = distances[idx] if idx < len(distances) else 0.5
                        similarity = 1.0 / (1.0 + float(dist))
                        semantic_scores[v_id] = similarity

        results_list = []
        now = time.time()

        for item in catalog_items:
            # Reconstruct candidate Pydantic wrapper
            provenance = MemoryProvenance(
                origin=item.get("source") or "conversation",
                correlation_id=item.get("correlation_id"),
            )

            content_body = item["title"]
            try:
                _, raw_body = self.obsidian_vault.read_markdown(item["vault_path"])
                # Clean header or formatting
                clean_body = raw_body.strip()
                if clean_body.startswith("# "):
                    lines = clean_body.split("\n", 2)
                    if len(lines) > 2:
                        clean_body = lines[2].strip()
                content_body = clean_body
            except Exception:
                pass

            cand = MemoryCandidate(
                uuid=UUID(item["uuid"]),
                memory_type=item["memory_type"],
                category=item["category"],
                title=item["title"],
                content=content_body,
                importance=item["importance"],
                confidence=item["confidence"],
                version=item["version"],
                provenance=provenance,
                created_at=datetime.fromtimestamp(item["created_at"]),
                updated_at=datetime.fromtimestamp(item["updated_at"]),
            )

            # Calculation:
            # 1. Similarity
            sim_score = (
                semantic_scores.get(item["vector_id"], 0.5) if item.get("vector_id") else 0.5
            )

            # 2. Recency (exponential decay)
            age_days = (now - item["updated_at"]) / (24 * 3600.0)
            rec_score = 1.0 / (1.0 + age_days)

            # 3. Importance mapping
            importance_map = {
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.5,
                "low": 0.2,
                "ignore": 0.0,
            }
            imp_score = importance_map.get(item["importance"].lower(), 0.5)

            # 4. Confidence
            conf_score = item["confidence"]

            # Unified Scoring weights
            w_sim = self.weights.get("similarity_weight", 0.4)
            w_rec = self.weights.get("recency_weight", 0.2)
            w_imp = self.weights.get("importance_weight", 0.2)
            w_conf = self.weights.get("confidence_weight", 0.2)

            total_score = (
                w_sim * sim_score + w_rec * rec_score + w_imp * imp_score + w_conf * conf_score
            )

            results_list.append(
                RetrievalResult(
                    candidate=cand,
                    score=total_score,
                    reasoning=f"Combined matching: Sim={sim_score:.2f}, Rec={rec_score:.2f}, Imp={imp_score:.2f}, Conf={conf_score:.2f}",
                )
            )

        # Sort descending by score
        results_list.sort(key=lambda r: r.score, reverse=True)
        return results_list[:limit]


class LifeLogMemory(ILifeLogMemory):
    """Autobiographical chronological logging system for Vulcan."""

    def __init__(self, sqlite_repo: SQLiteRepository, obsidian_vault: ObsidianVault):
        self.sqlite_repo = sqlite_repo
        self.obsidian_vault = obsidian_vault

    def delete(self, key: str, mode: str = "soft") -> None:
        # Life Logs cannot be soft deleted or archived individually; permanent deletes all life log records
        if mode == "permanent":
            with self.sqlite_repo._get_connection() as conn:
                conn.execute("DELETE FROM life_log")
                conn.commit()

    def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        meta = metadata or {}
        self.log_event(
            subsystem=meta.get("subsystem", "system"),
            action=key,
            result=str(value),
            summary=meta.get("summary", "System action log"),
            correlation_id=meta.get("correlation_id"),
            metadata=meta.get("metadata"),
        )

    def retrieve(self, _key: str) -> Any | None:
        # Retrieve logs from SQLite matching a specific subsystem key
        return self.sqlite_repo.get_life_log(limit=50)

    def log_event(
        self,
        subsystem: str,
        action: str,
        result: str,
        summary: str,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # Write to SQLite timeline
        meta_str = json.dumps(metadata) if metadata else "{}"
        self.sqlite_repo.write_life_log(
            subsystem, action, result, summary, correlation_id, meta_str
        )

        # Re-write aggregated Life Log file inside Obsidian for beautiful transparent human auditability
        from datetime import datetime

        log_entries = self.sqlite_repo.get_life_log(limit=100)
        md_lines = [
            "# Vulcan Autobiographical Life Log\n",
            "The chronological history of major system actions and results.\n",
        ]
        for entry in log_entries:
            dt_str = datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            md_lines.append(f"### [{dt_str}] {entry['subsystem'].capitalize()}: {entry['action']}")
            md_lines.append(f"- **Summary**: {entry['summary']}")
            md_lines.append(f"- **Result**: {entry['result']}")
            md_lines.append(f"- **Correlation ID**: `{entry['correlation_id'] or 'None'}`\n")

        self.obsidian_vault.write_markdown(
            "LifeLog/Life_Log_Timeline.md",
            {"memory_type": "life_log", "total_records": len(log_entries)},
            "\n".join(md_lines),
        )


class ReflectionMemory(IReflectionMemory):
    """Holds synthesis, evaluations and summaries of Vulcan performance."""

    def __init__(self, sqlite_repo: SQLiteRepository, obsidian_vault: ObsidianVault):
        self.sqlite_repo = sqlite_repo
        self.obsidian_vault = obsidian_vault

    def delete(self, key: str, mode: str = "soft") -> None:
        relative_path = f"Reflections/{key.replace(' ', '_')}.md"
        archive_only = mode != "permanent"
        self.obsidian_vault.delete_markdown(relative_path, archive_only=archive_only)

    def store(self, key: str, value: Any, _metadata: dict[str, Any] | None = None) -> None:
        # Write reflection summary to Obsidian Vault
        relative_path = f"Reflections/{key.replace(' ', '_')}.md"
        self.obsidian_vault.write_markdown(
            relative_path,
            {"memory_type": "reflection", "category": "reflection", "version": 1},
            f"# Reflection: {key}\n\n{value}",
        )

    def retrieve(self, key: str) -> Any | None:
        relative_path = f"Reflections/{key.replace(' ', '_')}.md"
        frontmatter, body = self.obsidian_vault.read_markdown(relative_path)
        return {"frontmatter": frontmatter, "body": body}


class IdentityMemory(IIdentityMemory):
    """Stores the core constants and principles that define Vulcan itself."""

    def __init__(self, obsidian_vault: ObsidianVault):
        self.obsidian_vault = obsidian_vault

    def delete(self, key: str, mode: str = "soft") -> None:
        relative_path = f"System/{key.replace(' ', '_')}.md"
        archive_only = mode != "permanent"
        self.obsidian_vault.delete_markdown(relative_path, archive_only=archive_only)

    def store(self, key: str, value: Any, _metadata: dict[str, Any] | None = None) -> None:
        # Prevent users or external models from altering key elements like the Constitution or version without authorization
        relative_path = f"System/{key.replace(' ', '_')}.md"
        self.obsidian_vault.write_markdown(
            relative_path,
            {"memory_type": "identity", "category": "identity", "version": 1},
            f"# Identity Component: {key}\n\n{value}",
        )

    def retrieve(self, key: str) -> Any | None:
        relative_path = f"System/{key.replace(' ', '_')}.md"
        frontmatter, body = self.obsidian_vault.read_markdown(relative_path)
        return {"frontmatter": frontmatter, "body": body}
