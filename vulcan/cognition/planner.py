"""Rule-based planner deciding how the cognitive loop handles each message."""

from typing import Any

from vulcan.cognition.models import DecisionType, PlannerDecision
from vulcan.services.inference import IInferenceProvider


class Planner:
    """Routes messages with deterministic rules; anything unmatched is answered directly."""

    def __init__(self, inference_provider: IInferenceProvider):
        self.inference_provider = inference_provider

    def make_decision(
        self, user_input: str, capabilities: dict[str, Any] | None = None
    ) -> PlannerDecision:
        """Determines the immediate orchestrator action (DirectResponse, ExecuteCapability, etc.)."""
        _ = capabilities  # Reserved for tool selection in the skills framework.
        # --- 1. Deterministic Rule Engine (Heuristics First) ---
        cleaned = user_input.strip()
        if not cleaned:
            return PlannerDecision(
                decision_type=DecisionType.REJECT_REQUEST,
                reasoning="Empty input request received.",
            )

        # UI commands / diagnostics commands
        if cleaned.lower() in ("shutdown", "shutdown system", "poweroff"):
            return PlannerDecision(
                decision_type=DecisionType.DEFER_EXECUTION,
                capability_name="ShutdownSystem",
                reasoning="User issued direct system shutdown command.",
            )

        if cleaned.lower() in ("diagnostics", "status", "system status"):
            return PlannerDecision(
                decision_type=DecisionType.DIRECT_RESPONSE,
                reasoning="Heuristics identified diagnostic query. Please review the visual panels.",
            )

        # Check for simple file reads / workspace actions
        if cleaned.lower().startswith("read file") or cleaned.lower().startswith("view file"):
            # Mock or direct mapping to a capability
            return PlannerDecision(
                decision_type=DecisionType.EXECUTE_CAPABILITY,
                capability_name="ExecuteCapability",
                arguments={"capability": "filesystem.read", "path": cleaned.split(" ", 2)[-1]},
                reasoning="Heuristic mapped user intent directly to filesystem.read.",
            )

        # --- 2. Default: answer directly ---
        # There is no LLM planning call: on CPU-only hardware every model call costs seconds,
        # so each message gets exactly one (the reply). Tool selection will move into that same
        # call via native tool calling when the skills framework lands.
        if not self.inference_provider.is_online():
            return PlannerDecision(
                decision_type=DecisionType.MODEL_UNAVAILABLE,
                reasoning="Local model provider is offline. Falling back gracefully.",
            )

        return PlannerDecision(
            decision_type=DecisionType.DIRECT_RESPONSE,
            reasoning="No rule matched; answering directly.",
        )


class MockPlanner(Planner):
    """Simple offline Mock planner for direct test execution without live model calls."""

    def make_decision(
        self, user_input: str, capabilities: dict[str, Any] | None = None
    ) -> PlannerDecision:
        _ = capabilities
        cleaned = user_input.strip()
        if cleaned.lower() == "test capability":
            return PlannerDecision(
                decision_type=DecisionType.EXECUTE_CAPABILITY,
                capability_name="ExecuteCapability",
                arguments={"capability": "filesystem.read"},
                reasoning="Directly mapped executing mock filesystem capability.",
            )
        return PlannerDecision(
            decision_type=DecisionType.DIRECT_RESPONSE,
            reasoning="Mock direct conversation response.",
        )
