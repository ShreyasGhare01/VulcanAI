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
    ):
        self.config = config
        self.registry = registry
        self.inference = inference

    def get_system_status(self) -> dict[str, Any]:
        """Provides status details for display inside the System Status panel."""
        from vulcan.utils.diagnostics import get_system_diagnostics

        diag = get_system_diagnostics()
        ollama_status = "Online" if self.inference.is_online() else "Offline"

        return {
            "app_name": self.config.app.name,
            "version": self.config.app.version,
            "debug_mode": str(self.config.app.debug),
            "environment": self.config.app.environment,
            "os": diag.get("os", "Unknown"),
            "cpu_count": diag.get("cpu_count", 1),
            "disk_free": f"{diag.get('disk_free_gb', 0)} GB",
            "ollama": ollama_status,
        }

    def get_registered_capabilities(self) -> dict[str, list[str]]:
        """Provides raw dictionary of capabilities registered across subsystems."""
        return self.registry.list_all_capabilities()

    def get_ollama_metrics(self) -> dict[str, Any]:
        """Queries local models and active endpoints."""
        if not self.inference.is_online():
            return {
                "status": "Offline",
                "version": "Unknown",
                "installed_count": 0,
                "running_count": 0,
            }

        try:
            return {
                "status": "Online",
                "version": self.inference.get_version() or "Unknown",
                "installed_count": len(self.inference.get_installed_models()),
                "running_count": len(self.inference.get_running_models()),
            }
        except Exception:
            return {
                "status": "Degraded",
                "version": "Unknown",
                "installed_count": 0,
                "running_count": 0,
            }


class MockUIController:
    """Mock controller for headlessly testing interface layouts without backend assembly."""

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
        }

    def get_registered_capabilities(self) -> dict[str, list[str]]:
        return {"filesystem.read": ["filesystem_skill"]}

    def get_ollama_metrics(self) -> dict[str, Any]:
        return {
            "status": "Offline",
            "version": "Unknown",
            "installed_count": 0,
            "running_count": 0,
        }
