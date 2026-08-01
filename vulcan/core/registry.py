"""Capability Registry interface and implementation."""

from abc import ABC, abstractmethod

from vulcan.core.models import Capability


class ICapabilityRegistry(ABC):
    """Interface for registering and querying capabilities in Vulcan."""

    @abstractmethod
    def register_capability(self, capability: Capability) -> None:
        """Registers a strongly-typed Capability model with its provider and metadata."""
        pass

    @abstractmethod
    def unregister_capability(self, capability_name: str, provider: str) -> None:
        """Unregisters a specific capability/provider mapping."""
        pass

    @abstractmethod
    def get_providers(self, capability_name: str) -> list[str]:
        """Lists providers supporting a given capability name (e.g. 'filesystem.read')."""
        pass

    @abstractmethod
    def has_capability(self, capability_name: str) -> bool:
        """Checks if any registered provider offers the requested capability."""
        pass

    @abstractmethod
    def list_all_capabilities(self) -> dict[str, list[str]]:
        """Lists all registered capabilities and their corresponding providers."""
        pass


class CapabilityRegistry(ICapabilityRegistry):
    """A concrete implementation of the Capability Registry using Pydantic Capability models."""

    def __init__(self) -> None:
        # Maps capability name -> {provider name: Capability model}
        self._registry: dict[str, dict[str, Capability]] = {}

    def register_capability(self, capability: Capability) -> None:
        if capability.name not in self._registry:
            self._registry[capability.name] = {}
        self._registry[capability.name][capability.provider] = capability

    def unregister_capability(self, capability_name: str, provider: str) -> None:
        if capability_name in self._registry:
            if provider in self._registry[capability_name]:
                del self._registry[capability_name][provider]
            if not self._registry[capability_name]:
                del self._registry[capability_name]

    def get_providers(self, capability_name: str) -> list[str]:
        return list(self._registry.get(capability_name, {}).keys())

    def has_capability(self, capability_name: str) -> bool:
        return capability_name in self._registry and len(self._registry[capability_name]) > 0

    def list_all_capabilities(self) -> dict[str, list[str]]:
        return {cap: list(provs.keys()) for cap, provs in self._registry.items()}
