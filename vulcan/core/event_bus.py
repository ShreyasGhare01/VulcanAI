"""Event bus interfaces and implementations for decoupled publish/subscribe communications."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from vulcan.core.service_lifecycle import LifecycleService
from vulcan.events import Event

EventHandler = Callable[[Event], Any]


class IEventBus(ABC):
    """Abstract interface defining the event subscription and distribution logic."""

    @abstractmethod
    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Subscribes an event handler to a hierarchical event namespace."""
        pass

    @abstractmethod
    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Unsubscribes an event handler from a hierarchical event namespace."""
        pass

    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publishes an event to all matched hierarchical subscribers."""
        pass


class EventBus(LifecycleService, IEventBus):
    """The central concrete event bus implementation for decoupling systems."""

    def __init__(self) -> None:
        super().__init__()
        self._subscribers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        if event_name in self._subscribers:
            try:
                self._subscribers[event_name].remove(handler)
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        # Match hierarchical exact topic names (e.g., 'System.Started')
        # Support cascading/wildcard namespaces (e.g. 'System.*' matches 'System.Started')
        for topic, handlers in list(self._subscribers.items()):
            matched = False
            if topic == "*" or topic == event.name:
                matched = True
            elif topic.endswith(".*"):
                prefix = topic[:-2]
                if event.name.startswith(prefix):
                    matched = True

            if matched:
                for handler in list(handlers):
                    try:
                        handler(event)
                    except Exception as e:
                        from vulcan.utils.logging import get_logger

                        get_logger("events").error(
                            f"Error executing event handler on {topic} for {event.name}: {e}"
                        )
