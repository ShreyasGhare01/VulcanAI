"""Definitive Phase 2 ACCEPTANCE TEST demonstrating full end-to-end memory loops."""

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
    """End-to-end lifecycle inference simulator returning custom payloads for validation."""

    def __init__(self) -> None:
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

        # 1. Extractor LLM prompt parsing
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

        # 2. Validation LLM prompt parsing
        if "Validator" in self.last_prompt:
            return InferenceResponse(
                assistant_message="""
                {
                  "importance": "high",
                  "confidence": 0.95
                }
                """,
                finish_reason="stop",
            )

        # 3. Session 1 Answer Generator
        if "favorite programming language is Python" in request.messages[-1]["content"]:
            return InferenceResponse(
                assistant_message="Got it! Python is now stored in my memory.",
                finish_reason="stop",
            )

        # 4. Session 2 Answer Generator
        if "What programming language do I prefer" in request.messages[-1]["content"]:
            # Ensure retrieved MemoryContextProvider piece reaches the prompt document
            if "Python" in self.last_prompt or any(
                "Python" in m["content"] for m in request.messages
            ):
                return InferenceResponse(
                    assistant_message="You told me you prefer Python.",
                    finish_reason="stop",
                )
            return InferenceResponse(
                assistant_message="I have no records of your preferred programming language.",
                finish_reason="stop",
            )

        return InferenceResponse(
            assistant_message="Hello!",
            finish_reason="stop",
        )

    def stream(self, request: InferenceRequest) -> Any:
        pass

    def get_capabilities(self) -> Any:
        pass


@pytest.fixture
def clean_test_workspace() -> Any:
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_phase2_persistent_memory_acceptance(clean_test_workspace: str) -> None:
    """Acceptance test verifying the full operational composition.

    It boot-composes all components:
    - Configuration
    - Event & Command Buses
    - MemoryManager (SQLite, Obsidian, MockChroma)
    - MemoryContextProvider
    - ContextAssemblyPipeline
    - PromptBuilder & Planner
    - CognitiveRouter
    """
    config = VulcanConfig()
    config.sqlite.db_path = os.path.join(clean_test_workspace, "vulcan_acceptance.db")
    config.obsidian.vault_path = os.path.join(clean_test_workspace, "obsidian_vault_acceptance")

    event_bus = EventBus()
    event_bus.initialize()
    command_bus = CommandBus()
    command_bus.initialize()

    inference = LifecycleMockInferenceProvider()
    chroma = MockChromaService()

    # Composed bootstrap
    memory_manager = MemoryManager(config, inference, event_bus, chroma)  # type: ignore

    session_manager = SessionManager()
    session_1 = session_manager.create_session(active_model="qwen2.5:latest")

    context_pipeline = ContextAssemblyPipeline()
    context_pipeline.register_provider(MemoryContextProvider(memory_manager))

    prompt_builder = PromptBuilder()
    planner = Planner(inference)

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

    # 1. Experience something & store it
    reply_1 = router.process_input("My favorite programming language is Python")
    assert "stored in my memory" in reply_1

    # Check files exist
    obsidian_file = os.path.join(
        config.obsidian.vault_path, "Users/Preference/Preferred_programming_language.md"
    )
    assert os.path.exists(obsidian_file)

    # 2. Start a clean separate Session (Cross-session recall)
    session_2 = session_manager.create_session(active_model="qwen2.5:latest")
    assert session_1.session_id != session_2.session_id

    # 3. Retrieve and utilize fact to construct response
    reply_2 = router.process_input("What programming language do I prefer?")
    assert "prefer Python" in reply_2
