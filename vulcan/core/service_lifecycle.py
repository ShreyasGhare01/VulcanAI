"""Lifecycle management contracts for long-lived systems in Vulcan AI OS."""

from abc import ABC, abstractmethod

from vulcan.core.models import HealthState, HealthStatus


class ILifecycle(ABC):
    """Lifecycle interface implemented by long-lived orchestrations and infrastructure services."""

    @abstractmethod
    def initialize(self) -> None:
        """Runs initial allocation, configuration validation, and workspace setup."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Begins execution loop, listener threads, or active service connectivity."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Suspends execution or releases connections temporarily."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Deallocates all resources cleanly and performs teardown tasks."""
        pass

    @abstractmethod
    def health(self) -> HealthStatus:
        """Reports the active service health and detailed telemetry diagnostic info."""
        pass


class LifecycleService(ILifecycle, ABC):
    """Convenient baseline implementation of ILifecycle."""

    def __init__(self) -> None:
        self._state: HealthState = HealthState.OFFLINE
        self._message: str = "Initialized but offline."

    def initialize(self) -> None:
        self._state = HealthState.INITIALIZING
        self._message = "Service is initializing."

    def start(self) -> None:
        self._state = HealthState.ONLINE
        self._message = "Service is online and active."

    def stop(self) -> None:
        self._state = HealthState.STOPPING
        self._message = "Service has stopped."

    def shutdown(self) -> None:
        self._state = HealthState.OFFLINE
        self._message = "Service shutdown completely."

    def health(self) -> HealthStatus:
        return HealthStatus(status=self._state, message=self._message)
