"""Structured context representation and composable context assembly pipeline."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ContextPriority(StrEnum):
    """Priority levels for context truncation."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"


class ContextPiece(BaseModel):
    """A standardized unit of operational context contributed by a context provider."""

    source: str
    type: str  # e.g., 'metadata', 'configuration', 'status', 'capabilities'
    priority: ContextPriority = ContextPriority.NORMAL
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content: Any  # Usually a string, dictionary, or validated sub-model
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def priority_weight(self) -> int:
        """Determines sorting precedence (lower is more important)."""
        mapping = {
            ContextPriority.CRITICAL: 1,
            ContextPriority.HIGH: 2,
            ContextPriority.NORMAL: 3,
            ContextPriority.LOW: 4,
            ContextPriority.BACKGROUND: 5,
        }
        return mapping.get(self.priority, 3)


class ContextBudgetManager:
    """Manages system context selection, truncation, and summarization policies."""

    def __init__(self, max_token_limit: int = 4096):
        self.max_token_limit = max_token_limit

    def manage_budget(self, pieces: list[ContextPiece]) -> list[ContextPiece]:
        """Decides which context pieces fit within budget constraints based on priorities."""
        # For Phase 1, we return all pieces, but sort them by priority_weight
        pieces.sort(key=lambda p: (p.priority_weight, p.timestamp))
        return pieces


class IContextProvider(ABC):
    """Interface for a modular, pluggable context source provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of this context provider."""
        pass

    @abstractmethod
    def provide_context(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        """Gathers and builds structured context pieces for inference."""
        pass


class ContextAssemblyPipeline:
    """Orchestrates registered context providers to compile full situational awareness."""

    def __init__(self) -> None:
        self._providers: dict[str, IContextProvider] = {}
        self.budget_manager = ContextBudgetManager()

    def register_provider(self, provider: IContextProvider) -> None:
        """Plugs in a context provider dynamically."""
        self._providers[provider.name] = provider

    def unregister_provider(self, name: str) -> None:
        """Unplugs a context provider."""
        if name in self._providers:
            del self._providers[name]

    def list_providers(self) -> list[str]:
        """Lists names of loaded providers."""
        return list(self._providers.keys())

    def assemble(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        """Runs the pipeline and returns a sorted list of context pieces."""
        assembled: list[ContextPiece] = []
        for provider in self._providers.values():
            try:
                pieces = provider.provide_context(session_id, **kwargs)
                assembled.extend(pieces)
            except Exception:
                # Robustly proceed even if one context provider errors
                pass

        # Route gathered pieces through budget allocation policies
        return self.budget_manager.manage_budget(assembled)


# --- Initial Context Providers ---


class SessionContextProvider(IContextProvider):
    """Contributes active conversation history and session attributes."""

    def __init__(self, session_manager: Any):
        self.session_manager = session_manager

    @property
    def name(self) -> str:
        return "session_context"

    def provide_context(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        _ = kwargs
        session = self.session_manager.get_session(session_id)
        if not session:
            return []

        content = {
            "session_id": session.session_id,
            "active_model": session.active_model,
            "active_task": session.active_task,
            "message_count": len(session.history),
            "total_tokens": session.total_tokens,
        }
        return [
            ContextPiece(
                source=self.name,
                type="session_metadata",
                priority=ContextPriority.HIGH,
                content=content,
            )
        ]


class ApplicationStatusProvider(IContextProvider):
    """Contributes application environmental status."""

    @property
    def name(self) -> str:
        return "application_status"

    def provide_context(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        _ = session_id
        _ = kwargs
        from vulcan.utils.diagnostics import get_system_diagnostics

        diag = get_system_diagnostics()
        return [
            ContextPiece(
                source=self.name,
                type="status",
                priority=ContextPriority.NORMAL,
                content=diag,
            )
        ]


class CurrentConfigurationProvider(IContextProvider):
    """Contributes current configuration details."""

    def __init__(self, config: Any):
        self.config = config

    @property
    def name(self) -> str:
        return "current_configuration"

    def provide_context(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        _ = session_id
        _ = kwargs
        content = {
            "app_name": self.config.app.name,
            "version": self.config.app.version,
            "debug": self.config.app.debug,
            "environment": self.config.app.environment,
            "workspace_dir": self.config.app.workspace_dir,
        }
        return [
            ContextPiece(
                source=self.name,
                type="configuration",
                priority=ContextPriority.NORMAL,
                content=content,
            )
        ]


class AvailableCapabilitiesProvider(IContextProvider):
    """Contributes currently registered capabilities from the CapabilityRegistry."""

    def __init__(self, registry: Any):
        self.registry = registry

    @property
    def name(self) -> str:
        return "available_capabilities"

    def provide_context(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        _ = session_id
        _ = kwargs
        caps = self.registry.list_all_capabilities()
        return [
            ContextPiece(
                source=self.name,
                type="capabilities",
                priority=ContextPriority.NORMAL,
                content=caps,
            )
        ]


class ActiveTaskProvider(IContextProvider):
    """Contributes information on the active task execution state (if any)."""

    def __init__(self, session_manager: Any):
        self.session_manager = session_manager

    @property
    def name(self) -> str:
        return "active_task"

    def provide_context(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        _ = kwargs
        session = self.session_manager.get_session(session_id)
        if not session or not session.active_task:
            return []

        return [
            ContextPiece(
                source=self.name,
                type="task",
                priority=ContextPriority.HIGH,
                content={"active_task_id": session.active_task},
            )
        ]


class IdentityContextProvider(IContextProvider):
    """Contributes core System identity attributes (philosophical core)."""

    def __init__(self, identity_provider: Any):
        self.identity_provider = identity_provider

    @property
    def name(self) -> str:
        return "identity_context"

    def provide_context(self, session_id: str, **kwargs: Any) -> list[ContextPiece]:
        _ = session_id
        _ = kwargs
        identity = self.identity_provider.assemble_identity()
        return [
            ContextPiece(
                source=self.name,
                type="identity",
                priority=ContextPriority.CRITICAL,  # Philosophy is critical
                content=identity,
            )
        ]
