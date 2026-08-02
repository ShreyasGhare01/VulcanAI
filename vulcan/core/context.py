"""Strongly-typed Pydantic context models for the Vulcan AI OS."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ConversationContext(BaseModel):
    """Context representing an active chat session or communication exchange with the user."""

    session_id: str
    user_id: str = "default_user"
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    active_tokens: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskContext(BaseModel):
    """Context governing a specific hierarchical task breakdown and execution parameters."""

    task_id: str
    parent_task_id: str | None = None
    priority: int = 1  # 1 (low) to 5 (critical)
    deadline: datetime | None = None
    dependencies: list[str] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)


class ExecutionContext(BaseModel):
    """Real-time system environment, resource utilization, and capabilities pathing context."""

    execution_id: str
    workspace_dir: str
    os_environment: dict[str, str] = Field(default_factory=dict)
    loaded_capabilities: list[str] = Field(default_factory=list)
    timeout_seconds: int = 30
    additional_resources: dict[str, Any] = Field(default_factory=dict)


class AgentContext(BaseModel):
    """Active runtime agent configurations, active personality overrides, and token budgets."""

    agent_id: str
    role: str
    current_persona: str
    max_token_budget: int = 4096
    temperature: float = 0.7
    system_prompts: list[str] = Field(default_factory=list)
    active_goals: list[str] = Field(default_factory=list)


class MemoryContext(BaseModel):
    """Context governing retrieval thresholds, vector limits, and temporary workspace facts."""

    session_id: str
    active_memory_domains: list[str] = Field(
        default_factory=lambda: [
            "working",
            "identity",
            "experience",
            "knowledge",
            "reflection",
            "development",
            "user",
        ]
    )
    vector_search_limit: int = 5
    similarity_threshold: float = 0.75
    temporary_scratchpad: dict[str, Any] = Field(default_factory=dict)
