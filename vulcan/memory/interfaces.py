"""Memory interfaces as defined in the architectural blueprint, including IUserMemory."""

from abc import ABC, abstractmethod
from typing import Any


class IMemory(ABC):
    """Base interface for a generic memory store."""

    @abstractmethod
    def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Stores a piece of information in this memory."""
        pass

    @abstractmethod
    def retrieve(self, key: str) -> Any | None:
        """Retrieves a piece of information by key."""
        pass


class IIdentityMemory(IMemory, ABC):
    """Identity memory interface, storing system identity, keys, configurations."""

    pass


class IExperienceMemory(IMemory, ABC):
    """Experience memory interface, logging chronological historical events/timeline."""

    pass


class IKnowledgeMemory(IMemory, ABC):
    """Knowledge memory interface, managing facts and static background information."""

    pass


class IWorkingMemory(IMemory, ABC):
    """Working memory interface, tracking the active task workflow context."""

    pass


class IReflectionMemory(IMemory, ABC):
    """Reflection memory interface, holding synthesis, evaluations and summaries."""

    pass


class IDevelopmentMemory(IMemory, ABC):
    """Development memory interface, tracking codebase structures, modules and tasks."""

    pass


class IUserMemory(IMemory, ABC):
    """User knowledge memory interface, representing the Obsidian-backed knowledge vault."""

    pass


class IMemoryManager(ABC):
    """The central manager coordinating operations across all memory subsystems."""

    @abstractmethod
    def get_identity_memory(self) -> IIdentityMemory:
        """Gets Identity Memory subsystem."""
        pass

    @abstractmethod
    def get_experience_memory(self) -> IExperienceMemory:
        """Gets Experience Memory subsystem."""
        pass

    @abstractmethod
    def get_knowledge_memory(self) -> IKnowledgeMemory:
        """Gets Knowledge Memory subsystem."""
        pass

    @abstractmethod
    def get_working_memory(self) -> IWorkingMemory:
        """Gets Working Memory subsystem."""
        pass

    @abstractmethod
    def get_reflection_memory(self) -> IReflectionMemory:
        """Gets Reflection Memory subsystem."""
        pass

    @abstractmethod
    def get_development_memory(self) -> IDevelopmentMemory:
        """Gets Development Memory subsystem."""
        pass

    @abstractmethod
    def get_user_memory(self) -> IUserMemory:
        """Gets Obsidian-backed IUserMemory subsystem."""
        pass
