"""Command Bus interface and implementation for routing active instructions."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from vulcan.core.command import Command
from vulcan.core.service_lifecycle import LifecycleService

CommandHandler = Callable[[Command], Any]


class ICommandBus(ABC):
    """Abstract interface for routing instruction commands."""

    @abstractmethod
    def register_handler(self, command_name: str, handler: CommandHandler) -> None:
        """Registers a single handler to execute when a command is dispatched."""
        pass

    @abstractmethod
    def unregister_handler(self, command_name: str) -> None:
        """Removes the registered handler for a command."""
        pass

    @abstractmethod
    def execute(self, command: Command) -> Any:
        """Dispatches a command to its registered handler, returning the execution result."""
        pass


class CommandBus(LifecycleService, ICommandBus):
    """Concrete CommandBus mapping hierarchical instruction names to handlers."""

    def __init__(self) -> None:
        super().__init__()
        self._handlers: dict[str, CommandHandler] = {}

    def register_handler(self, command_name: str, handler: CommandHandler) -> None:
        if command_name in self._handlers:
            raise KeyError(f"Command '{command_name}' already has a registered handler.")
        self._handlers[command_name] = handler

    def unregister_handler(self, command_name: str) -> None:
        if command_name in self._handlers:
            del self._handlers[command_name]

    def execute(self, command: Command) -> Any:
        # Hierarchical routing helper (e.g., 'Skill.Filesystem.Read')
        # Exact match route
        if command.name in self._handlers:
            return self._handlers[command.name](command)

        # Cascading match (e.g. 'Skill.Filesystem.*')
        for pattern, handler in self._handlers.items():
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if command.name.startswith(prefix):
                    return handler(command)

        raise KeyError(f"No command handler registered for command: '{command.name}'")
