"""Inference provider abstract interface and concrete OllamaProvider implementation."""

from abc import ABC, abstractmethod

import httpx

from vulcan.config import ModelConfig
from vulcan.core.models import HealthState, HealthStatus, ModelInfo
from vulcan.core.service_lifecycle import LifecycleService
from vulcan.utils.logging import get_logger


class IInferenceProvider(ABC):
    """Generic interface for local inference providers like Ollama, llama.cpp, vLLM."""

    @abstractmethod
    def is_online(self) -> bool:
        """Determines if the local inference provider HTTP server is active and responding."""
        pass

    @abstractmethod
    def get_version(self) -> str | None:
        """Queries the provider version."""
        pass

    @abstractmethod
    def get_installed_models(self) -> list[ModelInfo]:
        """Lists downloaded/installed models on the local instance."""
        pass

    @abstractmethod
    def get_running_models(self) -> list[ModelInfo]:
        """Lists models currently loaded in memory."""
        pass


class OllamaProvider(LifecycleService, IInferenceProvider):
    """resilient concrete implementation of IInferenceProvider mapping Ollama API endpoints."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.base_url = config.ollama_url.rstrip("/")
        self.timeout = config.timeout_seconds
        self.logger = get_logger("ollama_provider")

    def _get(self, endpoint: str) -> httpx.Response | None:
        """Performs a GET query, recovering gracefully from connectivity issues."""
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    return resp
        except Exception as e:
            self.logger.debug(f"Connection failure to Ollama endpoint {url}: {e}")
        return None

    def is_online(self) -> bool:
        resp = self._get("/")
        return resp is not None

    def get_version(self) -> str | None:
        resp = self._get("/api/version")
        if resp:
            try:
                data = resp.json()
                if isinstance(data, dict) and "version" in data:
                    val: str = data["version"]
                    return val
            except Exception as e:
                self.logger.error(f"Error parsing Ollama version json: {e}")
        return None

    def get_installed_models(self) -> list[ModelInfo]:
        resp = self._get("/api/tags")
        if resp:
            try:
                data = resp.json()
                if isinstance(data, dict) and "models" in data:
                    models_list = []
                    for m in data["models"]:
                        models_list.append(
                            ModelInfo(
                                name=m.get("name", "Unknown"),
                                version=m.get("details", {}).get("parameter_size", None),
                                size_bytes=m.get("size", None),
                                details=m,
                            )
                        )
                    return models_list
            except Exception as e:
                self.logger.error(f"Error parsing Ollama tags json: {e}")
        return []

    def get_running_models(self) -> list[ModelInfo]:
        resp = self._get("/api/ps")
        if resp:
            try:
                data = resp.json()
                if isinstance(data, dict) and "models" in data:
                    models_list = []
                    for m in data["models"]:
                        models_list.append(
                            ModelInfo(
                                name=m.get("name", "Unknown"),
                                version=None,
                                size_bytes=m.get("size", None),
                                details=m,
                            )
                        )
                    return models_list
            except Exception as e:
                self.logger.error(f"Error parsing Ollama ps json: {e}")
        return []

    def health(self) -> HealthStatus:
        if self.is_online():
            return HealthStatus(
                status=HealthState.ONLINE,
                message="Ollama inference provider is online.",
                details={"version": self.get_version() or "Unknown"},
            )
        return HealthStatus(
            status=HealthState.OFFLINE,
            message="Ollama local service is offline. Mark inference as offline.",
        )
