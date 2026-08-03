"""Strongly-typed response models, message types, and planning decisions for the Cognitive Core."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CognitiveState(StrEnum):
    """The explicit states within the Cognitive Loop lifecycle."""

    IDLE = "Idle"
    RECEIVING_INPUT = "ReceivingInput"
    BUILDING_CONTEXT = "BuildingContext"
    CONSTRUCTING_PROMPT = "ConstructingPrompt"
    INFERENCE_RUNNING = "InferenceRunning"
    PLANNING = "Planning"
    DISPATCHING_COMMAND = "DispatchingCommand"
    GENERATING_RESPONSE = "GeneratingResponse"
    UPDATING_SESSION = "UpdatingSession"
    COMPLETED = "Completed"


class MessageRole(StrEnum):
    """Roles present in conversation turns."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """An individual conversation message in a session."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    role: MessageRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserMessage(Message):
    """User message with fixed role."""

    role: MessageRole = MessageRole.USER


class AssistantMessage(Message):
    """Assistant message with fixed role."""

    role: MessageRole = MessageRole.ASSISTANT


class SystemMessage(Message):
    """System message with fixed role."""

    role: MessageRole = MessageRole.SYSTEM


class ConversationTurn(BaseModel):
    """A pair of user request and assistant response with timing/token details."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_message: Message
    assistant_message: Message
    metrics: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Standardized metadata block for deep metrics tracing
    latency_ms: float = 0.0
    inference_id: UUID = Field(default_factory=uuid4)
    planner_decision: str = "DirectResponse"
    context_provider_count: int = 0
    token_usage: int = 0
    model_name: str = ""
    execution_duration_ms: float = 0.0


class DecisionType(StrEnum):
    """Possible outcomes from the planning engine."""

    DIRECT_RESPONSE = "DirectResponse"
    EXECUTE_CAPABILITY = "ExecuteCapability"
    REQUEST_CLARIFICATION = "RequestClarification"
    REJECT_REQUEST = "RejectRequest"
    DEFER_EXECUTION = "DeferExecution"
    MODEL_UNAVAILABLE = "ModelUnavailable"

    # Reserved for future evolution
    CONSULT_MEMORY = "ConsultMemory"
    DELEGATE_AGENT = "DelegateAgent"
    REFLECT = "Reflect"
    SCHEDULE_TASK = "ScheduleTask"


class PlannerDecision(BaseModel):
    """A strongly typed outcome of a planning decision."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decision_type: DecisionType
    reasoning: str
    capability_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionSummary(BaseModel):
    """A high-level compiled summary of a conversation session."""

    session_id: str
    summary_text: str
    topics: list[str] = Field(default_factory=list)
    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
