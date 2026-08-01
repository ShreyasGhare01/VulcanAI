from vulcan.config import VulcanConfig
from vulcan.core.bootstrap import Bootstrapper
from vulcan.core.command_bus import ICommandBus
from vulcan.core.event_bus import IEventBus
from vulcan.core.registry import ICapabilityRegistry


def test_system_bootstrap_and_dependency_injection() -> None:
    bootstrapper = Bootstrapper()
    container = bootstrapper.boot()

    # Verify standard services exist in container
    assert container.has(VulcanConfig)
    assert container.has(IEventBus)
    assert container.has(ICommandBus)
    assert container.has(ICapabilityRegistry)

    # Verify standard registered capability
    registry = container.resolve(ICapabilityRegistry)
    assert registry.has_capability("System.Bootstrap")
    assert "Core.Bootstrapper" in registry.get_providers("System.Bootstrap")
