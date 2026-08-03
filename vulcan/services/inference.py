"""Inference provider abstract interface and concrete OllamaProvider implementation."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

import httpx
from pydantic import BaseModel, Field

from vulcan.config import ModelConfig
from vulcan.core.models import HealthState, HealthStatus, ModelInfo
from vulcan.core.service_lifecycle import LifecycleService
from vulcan.utils.logging import get_logger


class ProviderCapabilities(BaseModel):
    """The advertised support attributes of a model inference provider."""

    streaming: bool = True
    json_mode: bool = True
    tool_calling: bool = False
    vision: bool = False
    embeddings: bool = False
    function_calling: bool = False
    reasoning_tokens: bool = False


class InferenceMetrics(BaseModel):
    """Execution metrics for an inference request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    inference_duration_ms: float = 0.0


class InferenceRequest(BaseModel):
    """A strongly typed inference request package."""

    model: str
    system_prompt: str | None = None
    messages: list[dict[str, str]] = Field(default_factory=list)
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int | None = None
    stop: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    stream: bool = False


class InferenceResponse(BaseModel):
    """A strongly typed completed inference response package."""

    assistant_message: str
    finish_reason: str = "stop"
    metrics: InferenceMetrics = Field(default_factory=InferenceMetrics)
    raw_provider_metadata: dict[str, Any] = Field(default_factory=dict)


class InferenceStreamChunk(BaseModel):
    """A strongly typed incremental stream chunk."""

    content: str
    finish_reason: str | None = None
    metrics: InferenceMetrics | None = None
    raw_provider_metadata: dict[str, Any] = Field(default_factory=dict)


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

    @abstractmethod
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Executes a non-streaming chat generation request."""
        pass

    @abstractmethod
    def stream(self, request: InferenceRequest) -> Iterator[InferenceStreamChunk]:
        """Executes a streaming chat generation request, returning an iterator of chunks."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Returns the advertised capabilities supported by this provider instance."""
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

    def get_capabilities(self) -> ProviderCapabilities:
        # Ollama supports streaming, json_mode, and embeddings locally
        return ProviderCapabilities(
            streaming=True,
            json_mode=True,
            tool_calling=False,
            vision=False,
            embeddings=True,
            function_calling=False,
            reasoning_tokens=False,
        )

    def _build_ollama_payload(self, request: InferenceRequest) -> dict[str, Any]:
        """Translates the generic InferenceRequest into the format expected by /api/chat."""
        ollama_messages = []
        if request.system_prompt:
            ollama_messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            ollama_messages.append({"role": msg["role"], "content": msg["content"]})

        options: dict[str, Any] = {
            "temperature": request.temperature,
            "top_p": request.top_p,
        }
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        if request.stop is not None:
            options["stop"] = request.stop

        payload = {
            "model": request.model,
            "messages": ollama_messages,
            "stream": request.stream,
            "options": options,
        }
        return payload

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Executes a non-streaming chat request against Ollama's /api/chat."""
        import time

        start_time = time.perf_counter()

        if not self.is_online():
            from vulcan.core.exceptions import ModelError

            raise ModelError("Ollama local service is offline.")

        url = f"{self.base_url}/api/chat"
        payload = self._build_ollama_payload(request)
        payload["stream"] = False

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code != 200:
                    from vulcan.core.exceptions import ModelError

                    raise ModelError(f"Ollama returned status code {resp.status_code}: {resp.text}")

                data = resp.json()
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                assistant_content = data.get("message", {}).get("content", "")

                # Retrieve token counts and durational stats
                prompt_eval_count = data.get("prompt_eval_count", 0)
                eval_count = data.get("eval_count", 0)
                data.get("total_duration", 0)
                eval_duration_ns = data.get("eval_duration", 0)

                metrics = InferenceMetrics(
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    total_tokens=prompt_eval_count + eval_count,
                    latency_ms=latency_ms,
                    inference_duration_ms=(
                        eval_duration_ns / 1_000_000.0 if eval_duration_ns else latency_ms
                    ),
                )

                return InferenceResponse(
                    assistant_message=assistant_content,
                    finish_reason="stop",
                    metrics=metrics,
                    raw_provider_metadata=data,
                )
        except Exception as e:
            from vulcan.core.exceptions import ModelError

            self.logger.error(f"Ollama chat generation failed: {e}")
            raise ModelError(f"Ollama inference failure: {e}") from e

    def stream(self, request: InferenceRequest) -> Iterator[InferenceStreamChunk]:
        """Executes a streaming chat request against Ollama's /api/chat."""
        import json
        import time

        start_time = time.perf_counter()

        if not self.is_online():
            from vulcan.core.exceptions import ModelError

            raise ModelError("Ollama local service is offline.")

        url = f"{self.base_url}/api/chat"
        payload = self._build_ollama_payload(request)
        payload["stream"] = True

        try:
            # We use a custom stream client to retrieve line by line chunks
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload) as r:
                    if r.status_code != 200:
                        from vulcan.core.exceptions import ModelError

                        raise ModelError(f"Ollama stream returned status code {r.status_code}")

                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            done = data.get("done", False)

                            metrics = None
                            if done:
                                latency_ms = (time.perf_counter() - start_time) * 1000.0
                                prompt_eval_count = data.get("prompt_eval_count", 0)
                                eval_count = data.get("eval_count", 0)
                                eval_duration_ns = data.get("eval_duration", 0)

                                metrics = InferenceMetrics(
                                    prompt_tokens=prompt_eval_count,
                                    completion_tokens=eval_count,
                                    total_tokens=prompt_eval_count + eval_count,
                                    latency_ms=latency_ms,
                                    inference_duration_ms=(
                                        eval_duration_ns / 1_000_000.0
                                        if eval_duration_ns
                                        else latency_ms
                                    ),
                                )

                            yield InferenceStreamChunk(
                                content=content,
                                finish_reason="stop" if done else None,
                                metrics=metrics,
                                raw_provider_metadata=data,
                            )
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            from vulcan.core.exceptions import ModelError

            self.logger.error(f"Ollama stream generation failed: {e}")
            raise ModelError(f"Ollama stream inference failure: {e}") from e
