"""Hybrid Planning Engine evaluating user goals with rule-based and LLM-assisted models."""

import json
from typing import Any

from vulcan.cognition.models import DecisionType, PlannerDecision
from vulcan.services.inference import IInferenceProvider, InferenceRequest


class Planner:
    """Evaluates objectives using deterministic heuristics first, falling back to LLM inference."""

    def __init__(self, inference_provider: IInferenceProvider):
        self.inference_provider = inference_provider

    def make_decision(
        self, user_input: str, capabilities: dict[str, Any] | None = None
    ) -> PlannerDecision:
        """Determines the immediate orchestrator action (DirectResponse, ExecuteCapability, etc.)."""
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

        # --- 2. Fallback to LLM Planning ---
        if not self.inference_provider.is_online():
            return PlannerDecision(
                decision_type=DecisionType.MODEL_UNAVAILABLE,
                reasoning="Local model provider is offline. Falling back gracefully.",
            )

        # Let's prompt the model to return a structured planning decision in JSON
        system_prompt = (
            "You are Vulcan's core planning router. "
            "Your job is to decide whether to respond directly to the user or to invoke a capability. "
            "You MUST output raw JSON matching this structure and NO other text:\n"
            "{\n"
            '  "decision_type": "DirectResponse" | "ExecuteCapability" | "RequestClarification" | "RejectRequest",\n'
            '  "reasoning": "A concise explanation of why this decision was made",\n'
            '  "capability_name": "ExecuteCapability" or null,\n'
            '  "arguments": {}\n'
            "}"
        )

        prompt = (
            f"User input: {cleaned}\n"
            f"Available Capabilities: {list(capabilities.keys()) if capabilities else []}\n"
            f"Analyze the request and return the JSON decision."
        )

        try:
            req = InferenceRequest(
                model="llama3:latest",
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Highly deterministic
            )
            response = self.inference_provider.generate(req)
            data = json.loads(response.assistant_message)

            dtype_str = data.get("decision_type", "DirectResponse")
            # Ensure mapped correctly to enum value
            dtype = DecisionType.DIRECT_RESPONSE
            for val in DecisionType:
                if val.value == dtype_str:
                    dtype = val
                    break

            return PlannerDecision(
                decision_type=dtype,
                reasoning=data.get("reasoning", "Parsed from model response."),
                capability_name=data.get("capability_name"),
                arguments=data.get("arguments", {}),
            )
        except Exception as e:
            # Fallback to direct response if parsing or model fails
            return PlannerDecision(
                decision_type=DecisionType.DIRECT_RESPONSE,
                reasoning=f"LLM Planner raised parsing error or failed: {e}. Defaulting to direct reply.",
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
