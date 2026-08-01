"""Unit tests for Vulcan Context models."""

from datetime import datetime

from vulcan.core.context import (
    AgentContext,
    ConversationContext,
    ExecutionContext,
    MemoryContext,
    TaskContext,
)


def test_conversation_context_defaults() -> None:
    """Check defaults and initialization of ConversationContext."""
    ctx = ConversationContext(session_id="session-123")
    assert ctx.session_id == "session-123"
    assert ctx.user_id == "default_user"
    assert isinstance(ctx.started_at, datetime)
    assert ctx.active_tokens == 0
    assert ctx.metadata == {}


def test_task_context_validation() -> None:
    """Verify values inside TaskContext."""
    ctx = TaskContext(
        task_id="task-456",
        parent_task_id="parent-789",
        priority=3,
        variables={"step": "first"},
    )
    assert ctx.task_id == "task-456"
    assert ctx.parent_task_id == "parent-789"
    assert ctx.priority == 3
    assert ctx.variables == {"step": "first"}
    assert ctx.dependencies == []


def test_execution_context() -> None:
    """Verify values inside ExecutionContext."""
    ctx = ExecutionContext(
        execution_id="exec-abc",
        workspace_dir="./workspace",
        loaded_capabilities=["filesystem.read"],
    )
    assert ctx.execution_id == "exec-abc"
    assert ctx.workspace_dir == "./workspace"
    assert ctx.loaded_capabilities == ["filesystem.read"]
    assert ctx.timeout_seconds == 30


def test_agent_context() -> None:
    """Verify values inside AgentContext."""
    ctx = AgentContext(
        agent_id="agent-copilot",
        role="Developer Assistant",
        current_persona="Professional software engineer",
        max_token_budget=2048,
    )
    assert ctx.agent_id == "agent-copilot"
    assert ctx.role == "Developer Assistant"
    assert ctx.max_token_budget == 2048
    assert ctx.temperature == 0.7


def test_memory_context() -> None:
    """Verify values inside MemoryContext."""
    ctx = MemoryContext(session_id="session-123", vector_search_limit=10)
    assert ctx.session_id == "session-123"
    assert len(ctx.active_memory_domains) == 7
    assert ctx.vector_search_limit == 10
    assert ctx.similarity_threshold == 0.75
