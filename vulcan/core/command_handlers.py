"""Default lightweight handlers for domain-oriented system/capability commands."""

from typing import Any

from vulcan.core.command import Command
from vulcan.core.command_bus import ICommandBus
from vulcan.core.event_bus import IEventBus
from vulcan.events import Event


class SystemCommandHandler:
    """Standard system and capability command coordinator."""

    def __init__(self, command_bus: ICommandBus, event_bus: IEventBus):
        self.command_bus = command_bus
        self.event_bus = event_bus

    def initialize_standard_handlers(self) -> None:
        """Registers handlers for core domain actions."""
        self.command_bus.register_handler("ExecuteCapability", self.handle_execute_capability)
        self.command_bus.register_handler("ShutdownSystem", self.handle_shutdown_system)

    def handle_execute_capability(self, command: Command) -> Any:
        """Lightweight routing for requested system capabilities."""
        session_id = command.payload.get("session_id", "default")
        capability_name = command.payload.get("capability", "unknown")

        # Publish CapabilityNotImplemented as expected in Phase 1
        self.event_bus.publish(
            Event(
                name="Capability.ExecutionFailed",
                subsystem="orchestrator",
                data={
                    "session_id": session_id,
                    "capability": capability_name,
                    "reason": "CapabilityNotImplemented",
                },
            )
        )
        # Also log the command execution fact to Event Bus
        self.event_bus.publish(
            Event(
                name="Command.Executed",
                subsystem="orchestrator",
                data={
                    "command": "ExecuteCapability",
                    "capability": capability_name,
                },
            )
        )
        return {"status": "unimplemented", "capability": capability_name}

    def handle_shutdown_system(self, _command: Command) -> Any:
        """Fires safe shutdown logic."""
        self.event_bus.publish(
            Event(
                name="System.Stopped",
                subsystem="core",
                data={"reason": "User requested shutdown command."},
            )
        )
        self.event_bus.publish(
            Event(
                name="Command.Executed",
                subsystem="orchestrator",
                data={"command": "ShutdownSystem"},
            )
        )
        return {"status": "shutting_down"}
