"""Core service container interfaces and implementation for dependency injection."""

from abc import ABC, abstractmethod
from typing import Any


class IServiceContainer(ABC):
    """Abstract interface defining the dependency injection container."""

    @abstractmethod
    def register(self, interface: Any, implementation: Any) -> None:
        """Registers a service implementation bound to a specific interface or type."""
        pass

    @abstractmethod
    def resolve(self, interface: Any) -> Any:
        """Resolves a registered service implementation by its interface/type."""
        pass

    @abstractmethod
    def has(self, interface: Any) -> bool:
        """Checks whether a service is registered with the container."""
        pass


class ServiceContainer(IServiceContainer):
    """The concrete service container storing and resolving shared services."""

    def __init__(self) -> None:
        self._services: dict[Any, Any] = {}

    def register(self, interface: Any, implementation: Any) -> None:
        self._services[interface] = implementation

    def resolve(self, interface: Any) -> Any:
        if interface not in self._services:
            raise KeyError(f"Service '{interface}' is not registered in the container.")
        val: Any = self._services[interface]
        return val

    def has(self, interface: Any) -> bool:
        return interface in self._services
