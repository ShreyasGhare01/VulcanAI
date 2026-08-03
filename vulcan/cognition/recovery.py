"""Structured error recovery policies for the Cognitive Core loop."""

from collections.abc import Callable
from enum import StrEnum
from typing import Any


class ErrorRecoveryAction(StrEnum):
    """The action strategy prescribed by a recovery policy."""

    RETRY = "Retry"
    FALLBACK = "Fallback"
    ABORT = "Abort"
    NOTIFY_USER = "NotifyUser"
    CONTINUE_DEGRADED = "ContinueDegraded"


class ErrorRecoveryPolicy:
    """A policy governing how the system responds to a runtime exception."""

    def __init__(
        self,
        action: ErrorRecoveryAction = ErrorRecoveryAction.NOTIFY_USER,
        retry_count: int = 3,
        fallback_handler: Callable[..., Any] | None = None,
    ):
        self.action = action
        self.retry_count = retry_count
        self.fallback_handler = fallback_handler

    def attempt_recovery(self, error: Exception, *args: Any, **kwargs: Any) -> Any:
        """Executes the recovery strategy."""
        if self.action == ErrorRecoveryAction.RETRY:
            # Simulated retry loops
            pass
        elif self.action == ErrorRecoveryAction.FALLBACK and self.fallback_handler:
            return self.fallback_handler(error, *args, **kwargs)

        return self.action
