"""Regression tests for the Phase 2 hardening fixes.

Covers: memory query reaching the context pipeline, no hard-coded model names, the pending
memory queue keeping failed work, and a single blocking model call per user message.
"""

import os
import shutil
import tempfile
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from vulcan.cognition.context import ContextAssemblyPipeline, ContextPiece, IContextProvider
from vulcan.cognition.models import DecisionType
from vulcan.cognition.planner import Planner
from vulcan.cognition.prompt_builder import PromptBuilder
from vulcan.cognition.router import CognitiveRouter
from vulcan.cognition.session import SessionManager
from vulcan.config import ModelConfig, VulcanConfig
from vulcan.core.command_bus import CommandBus
from vulcan.core.event_bus import EventBus
from vulcan.core.exceptions import ModelError
from vulcan.memory.manager import MemoryManager
from vulcan.services.inference import (
    IInferenceProvider,
    InferenceRequest,
    InferenceResponse,
    OllamaProvider,
    ProviderCapabilities,
)


class RecordingInference(IInferenceProvider):
    """Records every generate() call; optionally fails them all."""

    def __init__(self, online: bool = True, fail: bool = False) -> None:
        self.online = online
        self.fail = fail
        self.requests: list[InferenceRequest] = []

    def is_online(self) -> bool:
        return self.online

    def get_version(self) -> str | None:
        return "test"

    def get_installed_models(self) -> list[Any]:
        return []

    def get_running_models(self) -> list[Any]:
        return []

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        if self.fail:
            raise ModelError("model went away")
        return InferenceResponse(assistant_message="[]")

    def stream(self, request: InferenceRequest) -> Iterator[Any]:
        _ = request
        return iter([])

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities()


class EmptyChroma:
    def is_available(self) -> bool:
        return False

    def get_collection(self, _name: str) -> Any:
        return None


class QueryRecordingProvider(IContextProvider):
    def __init__(self) -> None:
        self.seen_kwargs: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "query_recorder"

    def provide_context(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        _ = session_id
        self.seen_kwargs = kwargs
        return []


@pytest.fixture
def workspace() -> Iterator[str]:
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


def _config(workspace: str) -> VulcanConfig:
    config = VulcanConfig()
    config.sqlite.db_path = os.path.join(workspace, "vulcan.db")
    config.obsidian.vault_path = os.path.join(workspace, "vault")
    return config


def _router(
    inference: IInferenceProvider,
    pipeline: ContextAssemblyPipeline | None = None,
    memory_manager: Any = None,
) -> CognitiveRouter:
    return CognitiveRouter(
        session_manager=SessionManager(default_model="test-model:1b"),
        context_pipeline=pipeline or ContextAssemblyPipeline(),
        prompt_builder=PromptBuilder(),
        inference_provider=inference,
        planner=Planner(inference),
        command_bus=CommandBus(),
        event_bus=EventBus(),
        memory_manager=memory_manager,
    )


# --- Bug 1: the user's message must reach memory retrieval ---


def test_router_passes_user_input_to_context_pipeline() -> None:
    recorder = QueryRecordingProvider()
    pipeline = ContextAssemblyPipeline()
    pipeline.register_provider(recorder)

    _router(RecordingInference(), pipeline).process_input("What do I prefer?")

    assert recorder.seen_kwargs.get("user_input") == "What do I prefer?"


# --- Bug 2: no hard-coded model names ---


def test_default_model_is_qwen3_and_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    from vulcan.config import load_config

    assert ModelConfig().default_model == "qwen3:4b"
    monkeypatch.setenv("VULCAN_MODEL_DEFAULT_MODEL", "qwen3:1.7b")
    assert load_config().model.default_model == "qwen3:1.7b"


def test_boolean_env_override_parses_false(monkeypatch: pytest.MonkeyPatch) -> None:
    from vulcan.config import load_config

    monkeypatch.setenv("VULCAN_MODEL_DISABLE_THINKING", "false")
    assert load_config().model.disable_thinking is False


def test_reply_uses_session_model_and_disables_thinking() -> None:
    inference = RecordingInference()
    _router(inference).process_input("hello")

    assert len(inference.requests) == 1
    assert inference.requests[0].model == "test-model:1b"
    assert inference.requests[0].think is False


def test_memory_extraction_uses_configured_model(workspace: str) -> None:
    config = _config(workspace)
    config.model.default_model = "custom-model:2b"
    inference = RecordingInference()
    manager = MemoryManager(config, inference, EventBus(), EmptyChroma())  # type: ignore[arg-type]

    manager.council.evaluate_and_process("s1", "I use Linux", "Noted.")

    assert [r.model for r in inference.requests] == ["custom-model:2b"]
    assert inference.requests[0].think is False


# --- Bug 3: failed memory work stays queued ---


def test_failed_live_extraction_is_queued(workspace: str) -> None:
    inference = RecordingInference(fail=True)
    manager = MemoryManager(_config(workspace), inference, EventBus(), EmptyChroma())  # type: ignore[arg-type]

    manager.council.evaluate_and_process("s1", "My birthday is June 3", "Got it.")

    assert len(manager.sqlite_repo.get_pending_extractions()) == 1


def test_failed_pending_extraction_is_kept(workspace: str) -> None:
    inference = RecordingInference(fail=True)
    manager = MemoryManager(_config(workspace), inference, EventBus(), EmptyChroma())  # type: ignore[arg-type]
    manager.sqlite_repo.queue_extraction("s1", "My birthday is June 3", "Got it.")

    manager.council.process_pending_queue()
    assert len(manager.sqlite_repo.get_pending_extractions()) == 1

    inference.fail = False
    manager.council.process_pending_queue()
    assert manager.sqlite_repo.get_pending_extractions() == []


# --- Bug 4: one blocking model call per message ---


def test_planner_makes_no_model_call() -> None:
    inference = RecordingInference()
    decision = Planner(inference).make_decision("Tell me about the forge")

    assert decision.decision_type == DecisionType.DIRECT_RESPONSE
    assert inference.requests == []


def test_one_model_call_before_reply_then_memory_in_background(workspace: str) -> None:
    inference = RecordingInference()
    manager = MemoryManager(_config(workspace), inference, EventBus(), EmptyChroma())  # type: ignore[arg-type]
    router = _router(inference, memory_manager=manager)

    router.process_input("My favorite editor is VS Code")
    router.wait_for_background_tasks(timeout=30)
    router.shutdown()

    # Exactly two calls total: the reply, then one extraction (no planner, no validator call).
    systems = [r.system_prompt or "" for r in inference.requests]
    assert len(systems) == 2
    assert "Memory Extractor" not in systems[0]
    assert "Memory Extractor" in systems[1]


# --- Ollama payload ---


def test_ollama_payload_think_flag() -> None:
    provider = OllamaProvider(ModelConfig())
    with_flag = provider._build_ollama_payload(InferenceRequest(model="m", think=False))
    without_flag = provider._build_ollama_payload(InferenceRequest(model="m"))

    assert with_flag["think"] is False
    assert "think" not in without_flag


def test_ollama_generation_uses_long_timeout() -> None:
    provider = OllamaProvider(ModelConfig())
    assert isinstance(provider.generation_timeout, httpx.Timeout)
    assert provider.generation_timeout.read == 300
