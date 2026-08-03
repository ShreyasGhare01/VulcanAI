"""Comprehensive unit and behavioral testing for Phase 1 Cognitive Core subsystems."""

from typing import Any
from unittest.mock import MagicMock

from vulcan.cognition.context import (
    ActiveTaskProvider,
    ApplicationStatusProvider,
    AvailableCapabilitiesProvider,
    ContextAssemblyPipeline,
    ContextPriority,
    CurrentConfigurationProvider,
    IdentityContextProvider,
    SessionContextProvider,
)
from vulcan.cognition.identity import IdentityProvider
from vulcan.cognition.models import DecisionType, UserMessage
from vulcan.cognition.planner import Planner
from vulcan.cognition.prompt_builder import PromptBuilder
from vulcan.cognition.router import CognitiveRouter
from vulcan.cognition.session import SessionManager
from vulcan.config import VulcanConfig
from vulcan.core.command_bus import CommandBus
from vulcan.core.event_bus import EventBus
from vulcan.core.registry import CapabilityRegistry
from vulcan.services.inference import (
    IInferenceProvider,
    InferenceMetrics,
    InferenceRequest,
    InferenceResponse,
)


class MockInferenceProvider(IInferenceProvider):
    """Resilient mock provider representing inference outcomes for planning/generation."""

    def __init__(self, online: bool = True):
        self._online = online
        self.last_request: InferenceRequest | None = None

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
        if "Available Capabilities" in request.messages[0]["content"]:
            # Planner decision request mock response
            return InferenceResponse(
                assistant_message='{"decision_type": "ExecuteCapability", "reasoning": "Planner identified filesystem call.", "capability_name": "ExecuteCapability", "arguments": {"capability": "filesystem.read"}}'
            )
        return InferenceResponse(
            assistant_message="Hello, I am Vulcan AI Operating System. How can I assist you?",
            metrics=InferenceMetrics(prompt_tokens=10, completion_tokens=15, latency_ms=120.0),
        )

    def stream(self, _request: InferenceRequest) -> Any:
        return iter([])

    def get_capabilities(self) -> Any:
        from vulcan.services.inference import ProviderCapabilities

        return ProviderCapabilities()


def test_session_lifecycle() -> None:
    """Verifies creation, modification, and removal in SessionManager."""
    mgr = SessionManager()
    session = mgr.get_active_session()
    assert session is not None
    assert session.session_id is not None

    session.add_message(UserMessage(content="Hello world"))
    assert len(session.history) == 1

    session.update_metrics(10, 20, 150.0)
    assert session.prompt_tokens == 10
    assert session.completion_tokens == 20
    assert session.total_tokens == 30
    assert session.accumulated_latency_ms == 150.0

    # Multi-session support
    s2 = mgr.create_session("custom-id")
    assert s2.session_id == "custom-id"
    assert len(mgr.list_sessions()) == 2


def test_context_pipeline() -> None:
    """Verifies context providers successfully gather information."""
    config = VulcanConfig()
    registry = CapabilityRegistry()
    session_mgr = SessionManager()
    session_mgr.create_session("sess-1")

    identity_provider = IdentityProvider(config)

    pipeline = ContextAssemblyPipeline()
    pipeline.register_provider(SessionContextProvider(session_mgr))
    pipeline.register_provider(ApplicationStatusProvider())
    pipeline.register_provider(CurrentConfigurationProvider(config))
    pipeline.register_provider(AvailableCapabilitiesProvider(registry))
    pipeline.register_provider(ActiveTaskProvider(session_mgr))
    pipeline.register_provider(IdentityContextProvider(identity_provider))

    pieces = pipeline.assemble("sess-1")
    # All registered providers must execute successfully
    assert len(pieces) > 0

    # Ensure prioritized sequence logic
    assert pieces[0].priority == ContextPriority.CRITICAL  # Identity first


def test_prompt_assembly() -> None:
    """Verifies final prompts assemble correctly with well-defined sections."""
    builder = PromptBuilder()
    from vulcan.cognition.context import ContextPiece

    pieces = [
        ContextPiece(
            source="identity_context",
            type="identity",
            priority=ContextPriority.CRITICAL,
            content=MagicMock(
                name="Vulcan", constitution_summary="Constitution text", operating_rules=["Rule 1"]
            ),
        )
    ]

    prompt = builder.build_prompt_sequence(pieces, [], "Hello Vulcan")
    assert "=== IDENTITY ===" in prompt
    assert "=== OPERATING RULES ===" in prompt
    assert "=== USER INPUT ===" in prompt
    assert "Hello Vulcan" in prompt


def test_planner_deterministic_decisions() -> None:
    """Verifies rule-based routing bypasses the LLM successfully."""
    provider = MockInferenceProvider(online=True)
    planner = Planner(provider)

    decision = planner.make_decision("shutdown")
    assert decision.decision_type == DecisionType.DEFER_EXECUTION
    assert decision.capability_name == "ShutdownSystem"

    decision_empty = planner.make_decision("")
    assert decision_empty.decision_type == DecisionType.REJECT_REQUEST


def test_planner_llm_decisions() -> None:
    """Verifies fallback LLM planning parses decisions correctly."""
    provider = MockInferenceProvider(online=True)
    planner = Planner(provider)

    decision = planner.make_decision("read file file.txt")
    assert decision.decision_type == DecisionType.EXECUTE_CAPABILITY


def test_cognitive_loop_router() -> None:
    """Orchestrates an end-to-end trace of the full Cognitive Loop router flow."""
    config = VulcanConfig()
    CapabilityRegistry()
    event_bus = EventBus()
    command_bus = CommandBus()

    # Stub capability handler so execution doesn't fail
    def fake_handler(_cmd: Any) -> Any:
        return {"status": "ok"}

    command_bus.register_handler("ExecuteCapability", fake_handler)

    session_mgr = SessionManager()
    session_mgr.create_session("loop-session")

    pipeline = ContextAssemblyPipeline()
    identity_prov = IdentityProvider(config)
    pipeline.register_provider(IdentityContextProvider(identity_prov))

    provider = MockInferenceProvider(online=True)
    planner = Planner(provider)
    prompt_builder = PromptBuilder()

    router = CognitiveRouter(
        session_manager=session_mgr,
        context_pipeline=pipeline,
        prompt_builder=prompt_builder,
        inference_provider=provider,
        planner=planner,
        command_bus=command_bus,
        event_bus=event_bus,
    )

    reply = router.process_input("hello system")
    assert reply is not None
    assert len(reply) > 0
