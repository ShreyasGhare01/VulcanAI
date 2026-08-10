"""Memory Council orchestrator coordinating permanent memory evaluation."""

from typing import Any

from vulcan.core.event_bus import IEventBus
from vulcan.events import Event
from vulcan.memory.models import MemoryCandidate
from vulcan.memory.pipeline import (
    MemoryClassifier,
    MemoryConsolidator,
    MemoryExtractor,
    MemoryValidator,
)
from vulcan.memory.sqlite_store import SQLiteRepository
from vulcan.services.inference import IInferenceProvider
from vulcan.utils.logging import get_logger


class MemoryCouncil:
    """The central coordinator evaluating if candidates are worthy of permanent memory."""

    def __init__(
        self,
        inference_provider: IInferenceProvider,
        sqlite_repo: SQLiteRepository,
        event_bus: IEventBus,
        obsidian_vault: Any,
    ):
        self.inference_provider = inference_provider
        self.sqlite_repo = sqlite_repo
        self.event_bus = event_bus
        self.logger = get_logger("memory_council")

        # Core Pipeline Stages
        self.extractor = MemoryExtractor(inference_provider)
        self.classifier = MemoryClassifier()
        self.validator = MemoryValidator(inference_provider)
        self.consolidator = MemoryConsolidator(obsidian_vault)

        # Optional references injected by MemoryManager to prevent circular dependencies
        self.knowledge_memory: Any = None
        self.governance: Any = None

    def set_components(self, knowledge_memory: Any, governance: Any) -> None:
        """Injects store and governance dependencies."""
        self.knowledge_memory = knowledge_memory
        self.governance = governance

    def evaluate_and_process(
        self,
        session_id: str,
        user_input: str,
        assistant_response: str,
        correlation_id: str | None = None,
    ) -> list[MemoryCandidate]:
        """Orchestrates candidate extraction, evaluation, consolidation and filtering.

        If Ollama/inference is down, candidates are queued for offline extraction.
        """
        # Graceful degradation if model is down: Queue extraction in SQLite
        if not self.inference_provider.is_online():
            self.logger.info("Ollama is offline. Queueing interaction for offline extraction.")
            self.sqlite_repo.queue_extraction(session_id, user_input, assistant_response)
            self.event_bus.publish(
                Event(
                    name="Memory.ExtractionQueued",
                    subsystem="memory",
                    data={"session_id": session_id, "user_input": user_input},
                    correlation_id=correlation_id,
                )
            )
            return []

        # 1. Extractor
        candidates = self.extractor.extract_candidates(
            session_id, user_input, assistant_response, correlation_id
        )

        processed_memories = []
        for cand in candidates:
            # Publish Event: MemoryCandidateCreated
            self.event_bus.publish(
                Event(
                    name="MemoryCandidateCreated",
                    subsystem="memory",
                    data={"uuid": str(cand.uuid), "title": cand.title, "category": cand.category},
                    correlation_id=correlation_id,
                )
            )

            # 2. Classifier
            cand = self.classifier.classify(cand)

            # 3. Validator
            cand = self.validator.validate(cand)
            self.event_bus.publish(
                Event(
                    name="MemoryValidated",
                    subsystem="memory",
                    data={"uuid": str(cand.uuid), "importance": cand.importance, "confidence": cand.confidence},
                    correlation_id=correlation_id,
                )
            )

            # Ignore rule
            if cand.importance.lower().strip() == "ignore":
                self.logger.info(
                    f"Council ignored candidate: '{cand.title}' due to low importance."
                )
                self.event_bus.publish(
                    Event(
                        name="MemoryCandidateRejected",
                        subsystem="memory",
                        data={"uuid": str(cand.uuid), "reason": "Low importance"},
                        correlation_id=correlation_id,
                    )
                )
                continue

            # 4. Consolidator
            # Pull existing memories to check for duplicate or update versioning
            existing_records = []
            for item in self.sqlite_repo.list_catalog({"category": cand.category}):
                # Reconstruct placeholder Candidate to pass to consolidator
                from datetime import datetime
                from uuid import UUID

                from vulcan.memory.models import MemoryProvenance

                existing_records.append(
                    MemoryCandidate(
                        uuid=UUID(item["uuid"]),
                        memory_type=item["memory_type"],
                        category=item["category"],
                        title=item["title"],
                        content="",  # Minimal content
                        importance=item["importance"],
                        confidence=item["confidence"],
                        version=item["version"],
                        provenance=MemoryProvenance(correlation_id=item.get("correlation_id")),
                        created_at=datetime.fromtimestamp(item["created_at"]),
                        updated_at=datetime.fromtimestamp(item["updated_at"]),
                    )
                )

            cand = self.consolidator.consolidate(cand, existing_records)

            # 5. Governance Check and Conflict Resolution
            if self.governance:
                if not self.governance.approve_storage(cand):
                    self.logger.info(f"Memory Governance rejected candidate '{cand.title}'.")
                    self.event_bus.publish(
                        Event(
                            name="MemoryCandidateRejected",
                            subsystem="memory",
                            data={"uuid": str(cand.uuid), "reason": "Governance policy check failed"},
                            correlation_id=correlation_id,
                        )
                    )
                    continue

                if self.governance.detect_duplicates(cand):
                    self.logger.info(f"Duplicate candidate '{cand.title}' detected by Governance. Skipping.")
                    continue

                old_version = cand.version
                cand = self.governance.resolve_conflicts(cand) or cand
                if cand.version > old_version:
                    self.event_bus.publish(
                        Event(
                            name="MemoryConflictDetected",
                            subsystem="memory",
                            data={"uuid": str(cand.uuid), "old_version": old_version, "new_version": cand.version},
                            correlation_id=correlation_id,
                        )
                    )

            # 6. Storage Persistence Layer
            if self.knowledge_memory:
                is_update = cand.version > 1
                self.knowledge_memory.store(cand.title, cand)
                processed_memories.append(cand)

                # Publish Storage Events
                self.event_bus.publish(
                    Event(
                        name="MemoryUpdated" if is_update else "MemoryStored",
                        subsystem="memory",
                        data={"uuid": str(cand.uuid), "version": cand.version, "title": cand.title},
                        correlation_id=correlation_id,
                    )
                )

        return processed_memories

    def process_pending_queue(self) -> list[MemoryCandidate]:
        """Drains the pending offline queue and extracts memories when model is online."""
        if not self.inference_provider.is_online():
            return []

        pending = self.sqlite_repo.get_pending_extractions()
        if not pending:
            return []

        self.logger.info(f"Draining {len(pending)} pending offline extraction tasks...")
        extracted_total = []

        for record in pending:
            memories = self.evaluate_and_process(
                session_id=record["session_id"],
                user_input=record["user_input"],
                assistant_response=record["assistant_response"],
            )
            extracted_total.extend(memories)
            self.sqlite_repo.remove_pending_extraction(record["id"])

        return extracted_total


class MockVault:
    pass
