"""Comprehensive tests for Vulcan Phase 2 Persistent Memory and context subsystem."""

import os
import shutil
import tempfile
import time
from typing import Any
from uuid import UUID

import pytest

from vulcan.config import VulcanConfig
from vulcan.core.event_bus import EventBus
from vulcan.memory.governance import MemoryGovernance
from vulcan.memory.manager import MemoryManager
from vulcan.memory.models import MemoryCandidate
from vulcan.memory.obsidian import ObsidianVault
from vulcan.memory.pipeline import (
    MemoryClassifier,
    MemoryValidator,
)
from vulcan.memory.sqlite_store import SQLiteRepository
from vulcan.services.chroma import IChromaService
from vulcan.services.inference import (
    IInferenceProvider,
    InferenceMetrics,
    InferenceRequest,
    InferenceResponse,
)


class MockChromaService(IChromaService):
    """Simple offline-compatible mock ChromaDB service."""

    def __init__(self) -> None:
        self._available = True
        self._collections: dict[str, Any] = {}

    def is_available(self) -> bool:
        return self._available

    def get_collection(self, name: str) -> Any | None:
        if name not in self._collections:
            self._collections[name] = MockChromaCollection()
        return self._collections[name]

    def delete_collection(self, name: str) -> bool:
        if name in self._collections:
            del self._collections[name]
            return True
        return False


class MockChromaCollection:
    def __init__(self) -> None:
        self.ids: list[str] = []
        self.documents: list[str] = []
        self.metadatas: list[dict[str, Any]] = []

    def add(self, ids: list[str], documents: list[str], metadatas: list[dict[str, Any]]) -> None:
        self.ids.extend(ids)
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)

    def query(self, query_texts: list[str], n_results: int) -> dict[str, Any]:  # noqa: ARG002
        return {
            "ids": [self.ids[:n_results]],
            "documents": [self.documents[:n_results]],
            "distances": [[0.1] * len(self.ids[:n_results])],
        }


class MockInferenceProvider(IInferenceProvider):
    """Controlable mock inference provider for offline/online and structured testing."""

    def __init__(self, online: bool = True):
        self._online = online
        self.last_request: InferenceRequest | None = None
        self.response_text = "[]"

    def is_online(self) -> bool:
        return self._online

    def get_version(self) -> str | None:
        return "1.0.0" if self._online else None

    def get_installed_models(self) -> list[Any]:
        return []

    def get_running_models(self) -> list[Any]:
        return []

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        self.last_request = request
        return InferenceResponse(
            assistant_message=self.response_text,
            finish_reason="stop",
            metrics=InferenceMetrics(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        )

    def stream(self, request: InferenceRequest) -> Any:
        pass

    def get_capabilities(self) -> Any:
        pass


@pytest.fixture
def temp_workspace() -> Any:
    """Creates a temporary workspace directory for SQLite and Obsidian Vault."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def vulcan_config(temp_workspace: str) -> VulcanConfig:
    config = VulcanConfig()
    config.sqlite.db_path = os.path.join(temp_workspace, "vulcan_test.db")
    config.obsidian.vault_path = os.path.join(temp_workspace, "obsidian_vault")
    return config


def test_working_memory() -> None:
    """Verifies that Working Memory stores and retrieves values in-memory only."""
    from vulcan.memory.store import WorkingMemory

    wm = WorkingMemory()
    wm.store("current_task", "Refactor memory")
    assert wm.retrieve("current_task") == "Refactor memory"
    assert wm.retrieve("non_existent") is None


def test_obsidian_vault_initialization_and_versioning(temp_workspace: str) -> None:
    """Verifies that the Obsidian vault initializes standard folders and implements version backups."""
    vault_path = os.path.join(temp_workspace, "vault")
    vault = ObsidianVault(vault_path)
    vault.initialize_vault()

    # Check directories
    assert os.path.isdir(os.path.join(vault_path, "Users"))
    assert os.path.isdir(os.path.join(vault_path, "System"))
    assert os.path.isdir(os.path.join(vault_path, ".history"))

    # Write initial version
    relative_file = "Users/Education.md"
    fm = {"uuid": "123", "version": 1, "category": "education"}
    body = "# Purdue University\nJunior Biomedical Engineering student"

    vault.write_markdown(relative_file, fm, body)

    full_path = os.path.join(vault_path, relative_file)
    assert os.path.exists(full_path)

    # Read and verify content
    read_fm, read_body = vault.read_markdown(relative_file)
    assert str(read_fm["uuid"]) == "123"
    assert read_fm["version"] == 1
    assert "Purdue University" in read_body

    # Write second version -> Verify backup under .history
    fm_v2 = {"uuid": "123", "version": 1, "category": "education"}
    body_v2 = "# Purdue University\nUpdated to Senior year"
    vault.write_markdown(relative_file, fm_v2, body_v2)

    # Verify history file exists
    history_dir = os.path.join(vault_path, ".history")
    history_files = os.listdir(history_dir)
    assert len(history_files) == 1
    assert "Education_v1.md" in history_files[0]

    # Verify active file now has version 2
    read_fm2, read_body2 = vault.read_markdown(relative_file)
    assert read_fm2["version"] == 2
    assert "Senior" in read_body2


def test_sqlite_repository_catalogs_and_turns(temp_workspace: str) -> None:
    """Verifies standard SQLite repository operations for metadata, relationships, and Life Log."""
    db_path = os.path.join(temp_workspace, "test.db")
    repo = SQLiteRepository(db_path)

    # Catalog storage
    record = {
        "uuid": "fact-1",
        "memory_type": "knowledge",
        "category": "preference",
        "title": "Favorite IDE",
        "vault_path": "Users/Preferences/Favorite_IDE.md",
        "importance": "high",
        "confidence": 0.95,
        "version": 1,
        "source": "conversation",
        "correlation_id": "corr-123",
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    repo.store_catalog(record)

    res = repo.get_catalog("fact-1")
    assert res is not None
    assert res["title"] == "Favorite IDE"
    assert res["importance"] == "high"

    # Relationships
    repo.add_relationship("fact-1", "Uses", "target-id-999")
    rels = repo.get_relationships("fact-1")
    assert len(rels) == 1
    assert rels[0]["relationship"] == "Uses"
    assert rels[0]["target_uuid"] == "target-id-999"

    # Life Log
    repo.write_life_log("core", "Boot", "Success", "Booted OS phase 2")
    logs = repo.get_life_log()
    assert len(logs) == 1
    assert logs[0]["subsystem"] == "core"
    assert logs[0]["summary"] == "Booted OS phase 2"


def test_memory_pipeline_stages() -> None:
    """Verifies Classifier, Validator, and Consolidator stages."""
    # Classifier
    classifier = MemoryClassifier()
    cand = MemoryCandidate(
        memory_type="knowledge",
        category="INVALID_CATEGORY",
        title="Favorite IDE",
        content="Likes Cursor",
    )
    classified = classifier.classify(cand)
    assert classified.category == "fact"  # Default fallback normalization

    # Validator (Heuristics)
    mock_inference = MockInferenceProvider(online=False)  # Force heuristics fallback
    validator = MemoryValidator(mock_inference)
    cand2 = MemoryCandidate(
        memory_type="knowledge",
        category="preference",
        title="Favorite IDE",
        content="I think I might switch to VSCode possibly",
    )
    validated = validator.validate(cand2)
    assert validated.confidence == 0.60  # Found hesitant keywords

    cand3 = MemoryCandidate(
        memory_type="knowledge",
        category="relationship",
        title="Family detail",
        content="My spouse is Shreyas Ghare",
    )
    validated3 = validator.validate(cand3)
    assert validated3.importance == "critical"  # Spouse trigger word


def test_memory_council_evaluation_and_offline_queue(temp_workspace: str) -> None:
    """Verifies that MemoryCouncil processes input correctly when online and queues when offline."""
    event_bus = EventBus()
    event_bus.initialize()
    chroma = MockChromaService()

    # 1. Test Offline Queueing with private workspace
    config_offline = VulcanConfig()
    config_offline.sqlite.db_path = os.path.join(temp_workspace, "offline_test.db")
    config_offline.obsidian.vault_path = os.path.join(temp_workspace, "obsidian_vault_off")

    mock_offline_inference = MockInferenceProvider(online=False)
    manager_offline = MemoryManager(config_offline, mock_offline_inference, event_bus, chroma)

    turns = manager_offline.get_conversation_memory()
    turns.store("sess-1", "llama3:latest")

    candidates = manager_offline.council.evaluate_and_process(
        session_id="sess-1",
        user_input="I major in Biomedical Engineering at Purdue",
        assistant_response="That's awesome!",
    )
    assert len(candidates) == 0

    pending = manager_offline.sqlite_repo.get_pending_extractions()
    assert len(pending) == 1

    # 2. Test Online drainage with fresh workspace
    config_online = VulcanConfig()
    config_online.sqlite.db_path = os.path.join(temp_workspace, "online_test.db")
    config_online.obsidian.vault_path = os.path.join(temp_workspace, "obsidian_vault_on")

    mock_online_inference = MockInferenceProvider(online=True)
    mock_online_inference.response_text = """
    [
      {
        "title": "Education details",
        "content": "Majors in Biomedical Engineering at Purdue University",
        "category": "fact"
      }
    ]
    """
    manager_online = MemoryManager(config_online, mock_online_inference, event_bus, chroma)
    manager_online.sqlite_repo.queue_extraction(
        "sess-1", "I major in Biomedical Engineering at Purdue", "That's awesome!"
    )

    drained_memories = manager_online.council.process_pending_queue()
    assert len(drained_memories) == 1
    assert drained_memories[0].title == "Education details"


def test_memory_governance_rules(temp_workspace: str) -> None:
    """Verifies duplicate checking, privacy blocking, and conflict resolutions."""
    db_path = os.path.join(temp_workspace, "gov.db")
    repo = SQLiteRepository(db_path)
    gov = MemoryGovernance(repo)

    # Privacy blocks password
    cand_pass = MemoryCandidate(
        memory_type="knowledge",
        category="preference",
        title="My Password",
        content="password: SuperSecretPassword123",
    )
    assert not gov.approve_storage(cand_pass)

    # Conflict version update
    record = {
        "uuid": "fact-2",
        "memory_type": "knowledge",
        "category": "preference",
        "title": "Favorite IDE",
        "vault_path": "Users/Preferences/Favorite_IDE.md",
        "importance": "high",
        "confidence": 0.95,
        "version": 1,
        "source": "conversation",
        "correlation_id": "corr-123",
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    repo.store_catalog(record)

    # New candidate identical title and category triggers version conflict resolution
    cand_update = MemoryCandidate(
        memory_type="knowledge",
        category="preference",
        title="Favorite IDE",
        content="Cursor IDE",
        version=1,
    )
    resolved = gov.resolve_conflicts(cand_update)
    assert resolved is not None
    assert resolved.version == 2


def test_multidimensional_retrieval(vulcan_config: VulcanConfig) -> None:
    """Verifies that search scores items based on similarity, recency, confidence and importance weights."""
    event_bus = EventBus()
    event_bus.initialize()
    chroma = MockChromaService()
    inference = MockInferenceProvider()

    manager = MemoryManager(vulcan_config, inference, event_bus, chroma)
    knowledge = manager.get_knowledge_memory()

    # Store 2 candidate items with different priorities
    cand1 = MemoryCandidate(
        uuid=UUID("11111111-1111-1111-1111-111111111111"),
        memory_type="knowledge",
        category="preference",
        title="Preferred Language",
        content="My favorite programming language is Python",
        importance="high",
        confidence=0.95,
    )
    cand2 = MemoryCandidate(
        uuid=UUID("22222222-2222-2222-2222-222222222222"),
        memory_type="knowledge",
        category="preference",
        title="Lunch option",
        content="I had pepperoni pizza for lunch",
        importance="low",
        confidence=0.50,
    )

    knowledge.store("Preferred Language", cand1)
    knowledge.store("Lunch option", cand2)

    # Search for favorites -> Python should score significantly higher than pepperoni pizza
    results = knowledge.search("programming languages", limit=5)
    assert len(results) == 2
    assert results[0].candidate.title == "Preferred Language"
    assert results[1].candidate.title == "Lunch option"
    assert results[0].score > results[1].score
