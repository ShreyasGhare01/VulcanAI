"""Cognitive metrics collector and aggregator for session-level performance."""

from pydantic import BaseModel, Field


class CognitiveMetrics(BaseModel):
    """Aggregated statistics across multiple conversational runs."""

    average_latency_ms: float = 0.0
    average_response_time_ms: float = 0.0
    planner_distribution: dict[str, int] = Field(default_factory=dict)
    provider_uptime: float = 100.0  # Percentage online duration
    context_size: int = 0
    token_usage: int = 0
    active_sessions: int = 1
    commands_dispatched: int = 0
    events_published: int = 0
    provider_performance: dict[str, list[float]] = Field(default_factory=dict)
    conversation_count: int = 0

    def record_run(self, latency_ms: float, tokens: int, decision: str, provider: str) -> None:
        """Records a single inference loop and updates state metrics."""
        self.conversation_count += 1

        # Calculate moving averages
        self.average_latency_ms = (
            (self.average_latency_ms * (self.conversation_count - 1)) + latency_ms
        ) / self.conversation_count
        self.average_response_time_ms = self.average_latency_ms
        self.token_usage += tokens

        # Record distribution
        self.planner_distribution[decision] = self.planner_distribution.get(decision, 0) + 1

        # Record provider performance latency logs
        if provider not in self.provider_performance:
            self.provider_performance[provider] = []
        self.provider_performance[provider].append(latency_ms)

    def increment_commands(self) -> None:
        """Increments commands counter."""
        self.commands_dispatched += 1

    def increment_events(self) -> None:
        """Increments published events counter."""
        self.events_published += 1

    def update_sessions(self, count: int) -> None:
        """Sets active session count."""
        self.active_sessions = count
