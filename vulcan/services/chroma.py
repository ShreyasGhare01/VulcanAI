"""ChromaDB persistence service wrapper and interface definitions."""

import os
from abc import ABC, abstractmethod
from typing import Any

from vulcan.config import ChromaConfig
from vulcan.core.models import HealthState, HealthStatus
from vulcan.core.service_lifecycle import LifecycleService
from vulcan.utils.logging import get_logger


class IChromaService(ABC):
    """Abstract interface defining required ChromaDB persistent capabilities."""

    @abstractmethod
    def is_available(self) -> bool:
        """Determines if the ChromaDB database subsystem is available / functional."""
        pass

    @abstractmethod
    def get_collection(self, name: str) -> Any | None:
        """Gets or creates a ChromaDB vector collection."""
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """Deletes a ChromaDB vector collection by name."""
        pass


class ChromaService(LifecycleService, IChromaService):
    """Concrete implementation of the ChromaService client wrapper."""

    def __init__(self, config: ChromaConfig):
        super().__init__()
        self.persist_directory = config.persist_directory
        self.default_collection = config.collection_name
        self.logger = get_logger("chroma_service")
        self._client: Any | None = None
        self._available = False

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Dynamically imports and tries to instantiate PersistentClient of ChromaDB."""
        try:
            import chromadb

            os.makedirs(self.persist_directory, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_directory)
            self._available = True
            self._state = HealthState.ONLINE
            self._message = f"ChromaDB persistent service active at {self.persist_directory}."
        except Exception as e:
            self._available = False
            self._state = HealthState.DEGRADED
            self._message = f"ChromaDB offline or unavailable: {e}"

    def is_available(self) -> bool:
        return self._available

    def get_collection(self, name: str) -> Any | None:
        if not self._available or not self._client:
            return None
        try:
            return self._client.get_or_create_collection(name=name)
        except Exception:
            return None

    def delete_collection(self, name: str) -> bool:
        if not self._available or not self._client:
            return False
        try:
            self._client.delete_collection(name=name)
            return True
        except Exception:
            return False

    def health(self) -> HealthStatus:
        return HealthStatus(status=self._state, message=self._message)
