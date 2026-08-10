"""Central coordinator implementing IMemoryManager, exposing the six persistent memory systems."""

from typing import Any
from vulcan.config import VulcanConfig
from vulcan.core.event_bus import IEventBus
from vulcan.memory.council import MemoryCouncil
from vulcan.memory.interfaces import (
    IConversationMemory,
    IIdentityMemory,
    IKnowledgeMemory,
    ILifeLogMemory,
    IMemoryManager,
    IReflectionMemory,
    IWorkingMemory,
)
from vulcan.memory.obsidian import ObsidianVault
from vulcan.memory.sqlite_store import SQLiteRepository
from vulcan.memory.store import (
    ConversationMemory,
    IdentityMemory,
    KnowledgeMemory,
    LifeLogMemory,
    ReflectionMemory,
    WorkingMemory,
)
from vulcan.services.chroma import IChromaService
from vulcan.services.inference import IInferenceProvider
from vulcan.utils.logging import get_logger


class MemoryManager(IMemoryManager):
    """Authoritative memory manager, orchestrating accessors and coordinating the Memory Council pipeline."""

    def __init__(
        self,
        config: VulcanConfig,
        inference_provider: IInferenceProvider,
        event_bus: IEventBus,
        chroma_service: IChromaService,
    ):
        self.config = config
        self.logger = get_logger("memory_manager")

        # 1. Initialize SQLite catalog database
        self.sqlite_repo = SQLiteRepository(
            db_path=config.sqlite.db_path,
            timeout_seconds=config.sqlite.timeout_seconds,
        )

        # 2. Initialize Obsidian Vault
        self.obsidian_vault = ObsidianVault(vault_path=config.obsidian.vault_path)
        self.obsidian_vault.initialize_vault()

        # 3. Instantiate Subsystems
        self.working_memory = WorkingMemory()
        self.conversation_memory = ConversationMemory(self.sqlite_repo)

        # Setup multi-dimensional retrieval weights
        weights = {
            "similarity_weight": config.retrieval.similarity_weight,
            "recency_weight": config.retrieval.recency_weight,
            "importance_weight": config.retrieval.importance_weight,
            "confidence_weight": config.retrieval.confidence_weight,
        }
        self.knowledge_memory = KnowledgeMemory(
            self.sqlite_repo, chroma_service, self.obsidian_vault, weights
        )

        self.life_log_memory = LifeLogMemory(self.sqlite_repo, self.obsidian_vault)
        self.reflection_memory = ReflectionMemory(self.sqlite_repo, self.obsidian_vault)
        self.identity_memory = IdentityMemory(self.obsidian_vault)

        # 4. Initialize Memory Council Coordinator
        self.council = MemoryCouncil(
            inference_provider=inference_provider,
            sqlite_repo=self.sqlite_repo,
            event_bus=event_bus,
            obsidian_vault=self.obsidian_vault,
        )

        # Setup Memory Council injected references
        from vulcan.memory.governance import MemoryGovernance

        self.council.set_components(
            knowledge_memory=self.knowledge_memory, governance=MemoryGovernance(self.sqlite_repo)
        )

    def get_working_memory(self) -> IWorkingMemory:
        return self.working_memory

    def get_conversation_memory(self) -> IConversationMemory:
        return self.conversation_memory

    def get_knowledge_memory(self) -> IKnowledgeMemory:
        return self.knowledge_memory

    def get_life_log_memory(self) -> ILifeLogMemory:
        return self.life_log_memory

    def get_reflection_memory(self) -> IReflectionMemory:
        return self.reflection_memory

    def get_identity_memory(self) -> IIdentityMemory:
        return self.identity_memory

    def get_diagnostics(self) -> dict[str, Any]:
        """Provides raw diagnostics and health/record counters for Phase 2 memory systems."""
        import os

        # Check SQLite
        sqlite_ok = False
        record_count = 0
        pending_count = 0
        try:
            with self.sqlite_repo._get_connection() as conn:
                sqlite_ok = True
                row = conn.execute("SELECT COUNT(*) FROM memory_catalog").fetchone()
                record_count = row[0] if row else 0
                row_pending = conn.execute("SELECT COUNT(*) FROM pending_extractions").fetchone()
                pending_count = row_pending[0] if row_pending else 0
        except Exception:
            pass

        # Check Obsidian
        obsidian_ok = os.path.isdir(self.obsidian_vault.vault_path)

        # Check Chroma
        chroma_ok = self.knowledge_memory.chroma_service.is_available()

        return {
            "status": {
                "knowledge": "Online" if sqlite_ok and obsidian_ok else "Offline",
                "life_log": "Online" if sqlite_ok else "Offline",
                "obsidian": "Connected" if obsidian_ok else "Disconnected",
                "sqlite": "Connected" if sqlite_ok else "Disconnected",
                "chromadb": "Connected" if chroma_ok else "Disconnected",
            },
            "counts": {
                "memories": record_count,
                "pending": pending_count,
            },
        }
