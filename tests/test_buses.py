import pytest

from vulcan.core.command import Command
from vulcan.core.command_bus import CommandBus
from vulcan.core.event_bus import EventBus
from vulcan.events import Event


def test_hierarchical_event_bus() -> None:
    bus = EventBus()
    received = []

    def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe("System.*", handler)

    # Fits wildcard namespace
    bus.publish(Event("System.Started", "test"))
    bus.publish(Event("System.Shutdown", "test"))

    # Does not fit wildcard namespace
    bus.publish(Event("Skill.Loaded", "test"))

    assert len(received) == 2
    assert received[0].name == "System.Started"
    assert received[1].name == "System.Shutdown"


def test_command_bus_execution() -> None:
    bus = CommandBus()

    def read_handler(cmd: Command) -> str:
        return f"read: {cmd.payload.get('filepath')}"

    bus.register_handler("Skill.Filesystem.Read", read_handler)

    res = bus.execute(Command("Skill.Filesystem.Read", {"filepath": "abc.txt"}))
    assert res == "read: abc.txt"

    # Test duplicate handler raises KeyError
    with pytest.raises(KeyError):
        bus.register_handler("Skill.Filesystem.Read", read_handler)
