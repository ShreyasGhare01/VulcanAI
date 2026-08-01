"""Central bootstrapping orchestrator for booting up the Vulcan AI OS system."""

import os
from typing import Any

from vulcan.config import VulcanConfig, load_config
from vulcan.core.command_bus import CommandBus, ICommandBus
from vulcan.core.container import IServiceContainer, ServiceContainer
from vulcan.core.event_bus import EventBus, IEventBus
from vulcan.core.models import Capability, CapabilityStability
from vulcan.core.registry import CapabilityRegistry, ICapabilityRegistry
from vulcan.events import Event
from vulcan.utils.logging import get_logger, setup_logger


class Bootstrapper:
    """The central bootstrapper class.

    Assembles core services, validates config paths, registers capabilities,
    and publishes the System.Started event.
    """

    def __init__(
        self,
        config_dict: dict[str, Any] | None = None,
        config_filepath: str | None = None,
    ):
        self.config_dict = config_dict
        self.config_filepath = config_filepath
        self.container: IServiceContainer = ServiceContainer()
        self.logger = get_logger("bootstrap")

    def boot(self) -> IServiceContainer:
        """Sequential setup, registering base objects inside the ServiceContainer."""
        # 1. Load configuration
        config: VulcanConfig = load_config(self.config_dict, self.config_filepath)
        self.container.register(VulcanConfig, config)

        # 2. Setup Structured Logger
        setup_logger(config.logging)
        self.logger.info("Initializing Vulcan AI OS Bootstrap Phase...")

        # Ensure Workspace directories exist
        os.makedirs(config.app.workspace_dir, exist_ok=True)
        os.makedirs(os.path.dirname(config.logging.log_file_path), exist_ok=True)

        # 3. Create & Register Buses and Registries
        event_bus = EventBus()
        event_bus.initialize()
        self.container.register(IEventBus, event_bus)

        command_bus = CommandBus()
        command_bus.initialize()
        self.container.register(ICommandBus, command_bus)

        registry = CapabilityRegistry()
        self.container.register(ICapabilityRegistry, registry)

        # Register standard base capability
        base_cap = Capability(
            name="System.Bootstrap",
            version=config.app.version,
            description="Core Operating System boot capability.",
            provider="Core.Bootstrapper",
            stability=CapabilityStability.STABLE,
        )
        registry.register_capability(base_cap)

        # 4. Fire Hierarchical System.Started event
        event_bus.publish(
            Event(
                name="System.Started",
                subsystem="bootstrap",
                data={"name": config.app.name, "version": config.app.version},
            )
        )

        return self.container
