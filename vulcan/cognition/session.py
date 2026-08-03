"""Session structures and management layer for active conversations in Vulcan."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from vulcan.cognition.models import ConversationTurn, Message


class ConversationSession(BaseModel):
    """An active conversation session tracking history, metadata, and analytics."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    history: list[Message] = Field(default_factory=list)
    turns: list[ConversationTurn] = Field(default_factory=list)
    system_prompt: str | None = None
    active_model: str = "llama3:latest"
    active_task: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Token and latency counters
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    accumulated_latency_ms: float = 0.0
    inference_count: int = 0

    def add_message(self, message: Message) -> None:
        """Appends a message and updates the activity timestamp."""
        self.history.append(message)
        self.last_activity_at = datetime.now(UTC)

    def add_turn(self, turn: ConversationTurn) -> None:
        """Appends a structured turn to the list."""
        self.turns.append(turn)
        self.last_activity_at = datetime.now(UTC)

    def update_metrics(self, prompt_t: int, completion_t: int, latency_ms: float) -> None:
        """Updates cumulative token and latency stats."""
        self.prompt_tokens += prompt_t
        self.completion_tokens += completion_t
        self.total_tokens += prompt_t + completion_t
        self.accumulated_latency_ms += latency_ms
        self.inference_count += 1


class SessionManager:
    """Manages active conversation sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}
        self._active_session_id: str | None = None

    def create_session(
        self,
        session_id: str | None = None,
        system_prompt: str | None = None,
        active_model: str = "llama3:latest",
    ) -> ConversationSession:
        """Creates and tracks a new session."""
        sid = session_id or str(uuid4())
        session = ConversationSession(
            session_id=sid,
            system_prompt=system_prompt,
            active_model=active_model,
        )
        self._sessions[sid] = session
        if not self._active_session_id:
            self._active_session_id = sid
        return session

    def get_session(self, session_id: str) -> ConversationSession | None:
        """Retrieves a tracked session."""
        return self._sessions.get(session_id)

    def get_active_session(self) -> ConversationSession | None:
        """Returns the current active/focused session, creating one if empty."""
        if not self._active_session_id:
            session = self.create_session()
            self._active_session_id = session.session_id
        return self._sessions.get(self._active_session_id)

    def set_active_session(self, session_id: str) -> None:
        """Switches focus to a specific session."""
        if session_id in self._sessions:
            self._active_session_id = session_id

    def list_sessions(self) -> list[ConversationSession]:
        """Returns all tracked sessions."""
        return list(self._sessions.values())

    def delete_session(self, session_id: str) -> None:
        """Removes a session from tracking."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            if self._active_session_id == session_id:
                self._active_session_id = (
                    next(iter(self._sessions.keys())) if self._sessions else None
                )
