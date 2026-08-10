"""Cognitive Router (traffic controller) managing cognitive loop orchestration and state transitions."""

import time
from typing import Any
from uuid import uuid4

from vulcan.cognition.context import ContextAssemblyPipeline
from vulcan.cognition.models import (
    AssistantMessage,
    CognitiveState,
    ConversationTurn,
    DecisionType,
    PlannerDecision,
    UserMessage,
)
from vulcan.cognition.planner import Planner
from vulcan.cognition.prompt_builder import PromptBuilder
from vulcan.cognition.session import SessionManager
from vulcan.core.command import Command
from vulcan.core.command_bus import ICommandBus
from vulcan.core.event_bus import IEventBus
from vulcan.events import Event
from vulcan.services.inference import IInferenceProvider, InferenceRequest
from vulcan.utils.logging import get_logger


class CognitiveRouter:
    """The core traffic controller of the Vulcan Cognitive Loop and State Machine."""

    def __init__(
        self,
        session_manager: SessionManager,
        context_pipeline: ContextAssemblyPipeline,
        prompt_builder: PromptBuilder,
        inference_provider: IInferenceProvider,
        planner: Planner,
        command_bus: ICommandBus,
        event_bus: IEventBus,
        memory_manager: Any = None,
    ):
        self.session_manager = session_manager
        self.context_pipeline = context_pipeline
        self.prompt_builder = prompt_builder
        self.inference_provider = inference_provider
        self.planner = planner
        self.command_bus = command_bus
        self.event_bus = event_bus
        self.memory_manager = memory_manager
        self.logger = get_logger("cognitive_router")

    def _transition_state(
        self, state: CognitiveState, session_id: str, correlation_id: str
    ) -> None:
        """Helper to log and publish transitions on the Event Bus."""
        self.logger.debug(f"[Session: {session_id}] Transitioned to state: {state.value}")
        self.event_bus.publish(
            Event(
                name="Cognition.StateChanged",
                subsystem="cognition",
                data={"session_id": session_id, "state": state.value},
                correlation_id=correlation_id,
            )
        )

    def process_input(self, user_input: str) -> str:
        """Executes a single cycle of the cognitive loop."""
        session = self.session_manager.get_active_session()
        assert session is not None
        session_id = session.session_id

        # Generate a unique Correlation ID for tracing this interaction run
        correlation_id = str(uuid4())

        # Transition: RECEIVING_INPUT
        self._transition_state(CognitiveState.RECEIVING_INPUT, session_id, correlation_id)

        # Add user message to session
        user_msg = UserMessage(content=user_input)
        session.add_message(user_msg)

        # 1. Fire Event: Inference.Started
        self.event_bus.publish(
            Event(
                name="Inference.Started",
                subsystem="cognition",
                data={"session_id": session_id, "user_input": user_input},
                correlation_id=correlation_id,
            )
        )

        start_time = time.perf_counter()

        # 2. Transition: BUILDING_CONTEXT
        self._transition_state(CognitiveState.BUILDING_CONTEXT, session_id, correlation_id)
        context_pieces = self.context_pipeline.assemble(session_id)

        # 3. Transition: CONSTRUCTING_PROMPT
        self._transition_state(CognitiveState.CONSTRUCTING_PROMPT, session_id, correlation_id)
        system_instructions = self.prompt_builder.build_prompt_sequence(
            context_pieces, session.history[:-1], user_input
        )

        # 4. Transition: PLANNING
        self._transition_state(CognitiveState.PLANNING, session_id, correlation_id)
        capabilities_piece = next((p for p in context_pieces if p.type == "capabilities"), None)
        caps = capabilities_piece.content if capabilities_piece else {}
        decision: PlannerDecision = self.planner.make_decision(user_input, caps)

        # 5. Publish planning completion
        self.event_bus.publish(
            Event(
                name="Planning.Completed",
                subsystem="cognition",
                data={
                    "session_id": session_id,
                    "decision_type": decision.decision_type.value,
                    "reasoning": decision.reasoning,
                },
                correlation_id=correlation_id,
            )
        )

        # 6. Execute Router Decision
        final_assistant_text = ""
        prompt_tokens = 0
        completion_tokens = 0
        latency_ms = 0.0

        if decision.decision_type == DecisionType.MODEL_UNAVAILABLE:
            final_assistant_text = "Local model unavailable. Please verify Ollama is running."
        elif decision.decision_type == DecisionType.REJECT_REQUEST:
            final_assistant_text = f"Request Rejected: {decision.reasoning}"
        elif decision.decision_type == DecisionType.EXECUTE_CAPABILITY:
            # Transition: DISPATCHING_COMMAND
            self._transition_state(CognitiveState.DISPATCHING_COMMAND, session_id, correlation_id)

            # Construct a domain-oriented command to route via the Command Bus
            cmd_name = decision.capability_name or "ExecuteCapability"
            cmd_payload = decision.arguments
            cmd_payload["session_id"] = session_id

            try:
                cmd = Command(name=cmd_name, payload=cmd_payload)
                self.logger.info(f"Dispatching capability command to command bus: {cmd_name}")

                # Execute on Command Bus
                self.command_bus.execute(cmd)

                # Report action feedback directly
                final_assistant_text = f"Executing action: {decision.reasoning}"
            except Exception as e:
                final_assistant_text = f"Failed to execute command '{cmd_name}': {e}"
        else:
            # DIRECT_RESPONSE or similar -> generate response from LLM
            # Transition: GENERATING_RESPONSE
            self._transition_state(CognitiveState.GENERATING_RESPONSE, session_id, correlation_id)
            try:
                formatted_messages = self.prompt_builder.format_messages_for_provider(
                    system_prompt=system_instructions,
                    conversation_history=session.history[:-1],
                    current_user_input=user_input,
                )

                # Transition: INFERENCE_RUNNING
                self._transition_state(CognitiveState.INFERENCE_RUNNING, session_id, correlation_id)

                req = InferenceRequest(
                    model=session.active_model,
                    system_prompt=system_instructions,
                    messages=formatted_messages,
                    temperature=0.7,
                )

                response = self.inference_provider.generate(req)
                final_assistant_text = response.assistant_message

                prompt_tokens = response.metrics.prompt_tokens
                completion_tokens = response.metrics.completion_tokens
                latency_ms = response.metrics.latency_ms

                # Transition: UPDATING_SESSION
                self._transition_state(CognitiveState.UPDATING_SESSION, session_id, correlation_id)
                session.update_metrics(prompt_tokens, completion_tokens, latency_ms)

            except Exception as e:
                self.logger.error(f"Inference execution failed: {e}")
                final_assistant_text = f"Error generating response: {e}"

        # Complete turn tracking
        assistant_msg = AssistantMessage(content=final_assistant_text)
        session.add_message(assistant_msg)

        turn = ConversationTurn(
            user_message=user_msg,
            assistant_message=assistant_msg,
            metrics={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_ms": (time.perf_counter() - start_time) * 1000.0,
            },
            latency_ms=(time.perf_counter() - start_time) * 1000.0,
            planner_decision=decision.decision_type.value,
            context_provider_count=len(context_pieces),
            token_usage=prompt_tokens + completion_tokens,
            model_name=session.active_model,
            execution_duration_ms=(time.perf_counter() - start_time) * 1000.0,
        )
        session.add_turn(turn)

        # 7. Fire response generation complete events
        self.event_bus.publish(
            Event(
                name="Inference.Completed",
                subsystem="cognition",
                data={
                    "session_id": session_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                },
                correlation_id=correlation_id,
            )
        )
        self.event_bus.publish(
            Event(
                name="Response.Generated",
                subsystem="cognition",
                data={"session_id": session_id, "content": final_assistant_text},
                correlation_id=correlation_id,
            )
        )

        # 8. Invoke Memory Council to evaluate, extract, and persist long-term memories
        if self.memory_manager:
            try:
                self.logger.info("Invoking Memory Council to evaluate and extract facts...")
                self.memory_manager.council.evaluate_and_process(
                    session_id=session_id,
                    user_input=user_input,
                    assistant_response=final_assistant_text,
                    correlation_id=correlation_id,
                )
            except Exception as e:
                self.logger.error(f"Memory Council processing failed: {e}")

        # Transition: COMPLETED
        self._transition_state(CognitiveState.COMPLETED, session_id, correlation_id)

        # Transition: IDLE
        self._transition_state(CognitiveState.IDLE, session_id, correlation_id)

        return final_assistant_text
