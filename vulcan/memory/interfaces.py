"""Memory interfaces as defined in the architectural blueprint."""

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

    @abstractmethod
    def delete(self, key: str, mode: str = "soft") -> None:
        """Removes memory by unique identifier or search key with specific deletion semantics: soft, archive, permanent."""
        pass


class IWorkingMemory(IMemory, ABC):
    """Working memory interface, tracking the active task workflow context."""

    pass


class IConversationMemory(IMemory, ABC):
    """Conversation memory interface, storing non-permanent dialogue logs."""

    @abstractmethod
    def get_conversation_history(self, session_id: str) -> list[Any]:
        """Retrieves the list of messages or turns for a conversation session."""
        pass

    @abstractmethod
    def clear_conversation(self, session_id: str) -> None:
        """Clears/archives conversation history for a session."""
        pass


class IKnowledgeMemory(IMemory, ABC):
    """Long-Term Knowledge memory interface, managing structured facts and settings."""

    @abstractmethod
    def search(
        self, query: str, limit: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> list[Any]:
        """Performs multi-dimensional search combining similarity, recency, and metadata."""
        pass


class ILifeLogMemory(IMemory, ABC):
    """Life Log memory interface, recording chronological autobiography entries of Vulcan."""

    @abstractmethod
    def log_event(
        self,
        subsystem: str,
        action: str,
        result: str,
        summary: str,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Creates a structured life log entry."""
        pass


class IReflectionMemory(IMemory, ABC):
    """Reflection memory interface, holding synthesis, evaluations, and learned summaries."""

    pass


class IIdentityMemory(IMemory, ABC):
    """Identity memory interface, storing agent constitution, skills, and configuration."""

    pass


class IMemoryManager(ABC):
    """The central manager coordinating operations across all memory subsystems."""

    @abstractmethod
    def get_working_memory(self) -> IWorkingMemory:
        """Gets Working Memory subsystem."""
        pass

    @abstractmethod
    def get_conversation_memory(self) -> IConversationMemory:
        """Gets Conversation Memory subsystem."""
        pass

    @abstractmethod
    def get_knowledge_memory(self) -> IKnowledgeMemory:
        """Gets Knowledge Memory subsystem."""
        pass

    @abstractmethod
    def get_life_log_memory(self) -> ILifeLogMemory:
        """Gets Life Log Memory subsystem."""
        pass

    @abstractmethod
    def get_reflection_memory(self) -> IReflectionMemory:
        """Gets Reflection Memory subsystem."""
        pass

    @abstractmethod
    def get_identity_memory(self) -> IIdentityMemory:
        """Gets Identity Memory subsystem."""
        pass
