"""UI Controller layer to handle backend state mappings to display widgets using constructor injection."""

from typing import Any

from vulcan.config import VulcanConfig
from vulcan.core.registry import ICapabilityRegistry
from vulcan.services.inference import IInferenceProvider


class UIController:
    """Middle-layer controller separating backend business logic from raw PyQt views."""

    def __init__(
        self,
        config: VulcanConfig,
        registry: ICapabilityRegistry,
        inference: IInferenceProvider,
        cognitive_router: Any | None = None,
    ):
        self.config = config
        self.registry = registry
        self.inference = inference
        self.cognitive_router = cognitive_router

    def send_message(self, text: str) -> str:
        """Triggers the full backend Cognitive Loop flow for user input."""
        if self.cognitive_router:
            return str(self.cognitive_router.process_input(text))
        return f"[Cognitive Core Offline] Simulated response to: {text}"

    def get_system_status(self) -> dict[str, Any]:
        """Provides status details for display inside the System Status panel."""
        from vulcan.utils.diagnostics import get_system_diagnostics

        diag = get_system_diagnostics()
        ollama_status = "Online" if self.inference.is_online() else "Offline"

        active_session = None
        session_count = 0
        if self.cognitive_router and self.cognitive_router.session_manager:
            session_count = len(self.cognitive_router.session_manager.list_sessions())
            active_session = self.cognitive_router.session_manager.get_active_session()

        return {
            "app_name": self.config.app.name,
            "version": self.config.app.version,
            "debug_mode": str(self.config.app.debug),
            "environment": self.config.app.environment,
            "os": diag.get("os", "Unknown"),
            "cpu_count": diag.get("cpu_count", 1),
            "disk_free": f"{diag.get('disk_free_gb', 0)} GB",
            "ollama": ollama_status,
            "session_count": session_count,
            "active_session": active_session.session_id if active_session else "None",
            "planner_status": "Online/Hybrid" if self.cognitive_router else "Offline",
            "event_bus": "Online",
            "command_bus": "Online",
        }

    def get_registered_capabilities(self) -> dict[str, list[str]]:
        """Provides raw dictionary of capabilities registered across subsystems."""
        return self.registry.list_all_capabilities()

    def get_ollama_metrics(self) -> dict[str, Any]:
        """Queries local models and active endpoints."""
        active_provider = "Ollama"
        loaded_model = self.config.model.default_model
        latency = "0.0 ms"
        token_usage = "0"

        if self.cognitive_router and self.cognitive_router.session_manager:
            session = self.cognitive_router.session_manager.get_active_session()
            if session:
                loaded_model = session.active_model
                latency = f"{session.accumulated_latency_ms:.1f} ms"
                token_usage = str(session.total_tokens)

        if not self.inference.is_online():
            return {
                "status": "Offline",
                "active_provider": active_provider,
                "loaded_model": loaded_model,
                "latency": latency,
                "token_usage": token_usage,
                "installed_count": 0,
                "running_count": 0,
            }

        try:
            return {
                "status": "Online",
                "active_provider": active_provider,
                "loaded_model": loaded_model,
                "latency": latency,
                "token_usage": token_usage,
                "installed_count": len(self.inference.get_installed_models()),
                "running_count": len(self.inference.get_running_models()),
            }
        except Exception:
            return {
                "status": "Degraded",
                "active_provider": active_provider,
                "loaded_model": loaded_model,
                "latency": latency,
                "token_usage": token_usage,
                "installed_count": 0,
                "running_count": 0,
            }


class MockUIController:
    """Mock controller for headlessly testing interface layouts without backend assembly."""

    def send_message(self, text: str) -> str:
        return f"[Mock] Response to: {text}"

    def get_system_status(self) -> dict[str, Any]:
        return {
            "app_name": "Vulcan Test OS",
            "version": "0.1.0",
            "debug_mode": "True",
            "environment": "testing",
            "os": "TestOS",
            "cpu_count": 4,
            "disk_free": "100 GB",
            "ollama": "Offline",
            "session_count": 1,
            "active_session": "test-session-id",
            "planner_status": "Online/Hybrid",
            "event_bus": "Online",
            "command_bus": "Online",
        }

    def get_registered_capabilities(self) -> dict[str, list[str]]:
        return {"filesystem.read": ["filesystem_skill"]}

    def get_ollama_metrics(self) -> dict[str, Any]:
        return {
            "status": "Offline",
            "active_provider": "Ollama",
            "loaded_model": "llama3:latest",
            "latency": "0.0 ms",
            "token_usage": "0",
            "installed_count": 0,
            "running_count": 0,
        }
