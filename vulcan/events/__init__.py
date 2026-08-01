"""Central communication back-bone interfaces and events definitions."""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict


@dataclass(frozen=True)
class Event:
    """Base Event payload structure for all pub/sub events."""

    name: str
    subsystem: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
