"""End-to-End Integration Test for Phase 2 Memory and Cognitive Loop Lifecycle."""

import os
import shutil
import tempfile
from typing import Any

import pytest

from vulcan.cognition.context import ContextAssemblyPipeline, MemoryContextProvider
from vulcan.cognition.planner import Planner
from vulcan.cognition.prompt_builder import PromptBuilder
from vulcan.cognition.router import CognitiveRouter
from vulcan.cognition.session import SessionManager
from vulcan.config import VulcanConfig
from vulcan.core.command_bus import CommandBus
from vulcan.core.event_bus import EventBus
from vulcan.memory.manager import MemoryManager
from vulcan.services.inference import (
    IInferenceProvider,
    InferenceRequest,
    InferenceResponse,
)


class MockChromaService:
    def __init__(self) -> None:
        self._available = True
        self._collection = MockChromaCollection()

    def is_available(self) -> bool:
        return self._available

    def get_collection(self, _name: str) -> Any:
        return self._collection


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


class LifecycleMockInferenceProvider(IInferenceProvider):
    """Resilient mock that mimics distinct LLM outputs for each phase of the integration test."""

    def __init__(self) -> None:
        self.session_phase = 1
        self.last_prompt = ""

    def is_online(self) -> bool:
        return True

    def get_version(self) -> str:
        return "1.0.0"

    def get_installed_models(self) -> list[Any]:
        return []

    def get_running_models(self) -> list[Any]:
        return []

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        self.last_prompt = request.system_prompt or ""

        # Phase 1: Memory Extraction LLM response
        if "Memory Extractor" in self.last_prompt:
            return InferenceResponse(
                assistant_message="""
                [
                  {
                    "title": "Preferred programming language",
                    "content": "My favorite programming language is Python",
                    "category": "preference"
                  }
                ]
                """,
                finish_reason="stop",
            )

        # Phase 2: Memory Validation LLM response
        if "Validator" in self.last_prompt or "confidence" in request.messages[0]["content"]:
            return InferenceResponse(
                assistant_message="""
                {
                  "importance": "high",
                  "confidence": 0.95
                }
                """,
                finish_reason="stop",
            )

        # Phase 3: Conversational Response generation
        # Session 1 conversational reply
        if "favorite programming language is Python" in request.messages[-1]["content"]:
            return InferenceResponse(
                assistant_message="Got it! I will remember that Python is your favorite programming language.",
                finish_reason="stop",
            )

        # Session 2 conversational reply (where it should answer based on injected memory context)
        if "What programming language do I prefer" in request.messages[-1]["content"]:
            # Check if Python is injected in system prompts/context messages
            if "Python" in self.last_prompt or any(
                "Python" in m["content"] for m in request.messages
            ):
                return InferenceResponse(
                    assistant_message="Based on what you told me, you prefer Python.",
                    finish_reason="stop",
                )
            else:
                return InferenceResponse(
                    assistant_message="I'm not sure what language you prefer.",
                    finish_reason="stop",
                )

        return InferenceResponse(
            assistant_message="Hello, I am Vulcan.",
            finish_reason="stop",
        )

    def stream(self, request: InferenceRequest) -> Any:
        pass

    def get_capabilities(self) -> Any:
        pass


@pytest.fixture
def clean_workspace() -> Any:
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_complete_cognitive_memory_lifecycle(clean_workspace: str) -> None:
    """End-to-End demonstration that Memory is no longer merely infrastructure.

    It validates:
    - Session 1: User says: 'My favorite programming language is Python.'
    - Memory is extracted, validated by Governance, and stored in SQLite + Obsidian.
    - Session 2: User asks: 'What programming language do I prefer?'
    - The MemoryContextProvider retrieves it, context is assembled, PromptBuilder structures it,
      and Vulcan responds with 'Python' based on its stored memory.
    """
    # 1. Config & Core boot
    config = VulcanConfig()
    config.sqlite.db_path = os.path.join(clean_workspace, "vulcan_e2e.db")
    config.obsidian.vault_path = os.path.join(clean_workspace, "obsidian_vault_e2e")

    event_bus = EventBus()
    event_bus.initialize()
    command_bus = CommandBus()
    command_bus.initialize()

    inference = LifecycleMockInferenceProvider()
    chroma = MockChromaService()

    # 2. Setup MemoryManager & Context Assembly Pipeline
    memory_manager = MemoryManager(config, inference, event_bus, chroma)  # type: ignore

    session_manager = SessionManager()
    session = session_manager.create_session(active_model="llama3:latest")

    context_pipeline = ContextAssemblyPipeline()
    # Register our new MemoryContextProvider
    memory_provider = MemoryContextProvider(memory_manager)
    context_pipeline.register_provider(memory_provider)

    prompt_builder = PromptBuilder()
    planner = Planner(inference)

    # Instantiate Router with injected MemoryManager
    router = CognitiveRouter(
        session_manager=session_manager,
        context_pipeline=context_pipeline,
        prompt_builder=prompt_builder,
        inference_provider=inference,
        planner=planner,
        command_bus=command_bus,
        event_bus=event_bus,
        memory_manager=memory_manager,
    )

    # ==================== SESSION 1: SAVING MEMORY ====================
    user_input_1 = "My favorite programming language is Python"
    reply_1 = router.process_input(user_input_1)

    assert "I will remember that Python is your favorite" in reply_1

    # Verify memory was cataloged and stored in SQLite + Obsidian
    catalog_items = memory_manager.sqlite_repo.list_catalog({"category": "preference"})
    assert len(catalog_items) == 1
    assert catalog_items[0]["title"] == "Preferred programming language"
    assert catalog_items[0]["importance"] == "high"

    # Verify Obsidian file was generated
    obsidian_file_path = os.path.join(
        config.obsidian.vault_path, "Users/Preference/Preferred_programming_language.md"
    )
    assert os.path.exists(obsidian_file_path)

    # Read Obsidian and check frontmatter
    fm, body = memory_manager.obsidian_vault.read_markdown(
        "Users/Preference/Preferred_programming_language.md"
    )
    assert fm["category"] == "preference"
    assert fm["version"] == 1
    assert "Python" in body

    # ==================== SESSION 2: RETRIEVING MEMORY ====================
    # Start a brand new clean session to verify persistent recall across sessions!
    session_2 = session_manager.create_session(active_model="llama3:latest")
    assert session_2.session_id != session.session_id

    # The user asks about their preference
    user_input_2 = "What programming language do I prefer?"

    # Context assembly should invoke MemoryContextProvider, matching query with stored catalog
    pieces = context_pipeline.assemble(session_2.session_id, user_input=user_input_2)
    assert len(pieces) == 1
    assert pieces[0].type == "long_term_knowledge"
    assert "Python" in str(pieces[0].content)

    # Run loop for session 2
    reply_2 = router.process_input(user_input_2)
    assert "you prefer Python" in reply_2
