from vulcan.config import ModelConfig
from vulcan.core.models import Capability, CapabilityStability
from vulcan.core.registry import CapabilityRegistry
from vulcan.services.inference import OllamaProvider


def test_capability_registry_with_pydantic_models() -> None:
    registry = CapabilityRegistry()
    assert not registry.has_capability("filesystem.read")

    cap = Capability(
        name="filesystem.read",
        description="Allows reading files",
        provider="filesystem_skill",
        required_permissions=["filesystem.read"],
        stability=CapabilityStability.STABLE,
    )
    registry.register_capability(cap)

    assert registry.has_capability("filesystem.read")
    assert "filesystem_skill" in registry.get_providers("filesystem.read")

    all_caps = registry.list_all_capabilities()
    assert "filesystem.read" in all_caps
    assert all_caps["filesystem.read"] == ["filesystem_skill"]


def test_ollama_provider_offline_graceful_fallback() -> None:
    config = ModelConfig()
    config.ollama_url = "http://localhost:59999"
    config.timeout_seconds = 1
    provider = OllamaProvider(config)

    assert provider.is_online() is False
    assert provider.get_version() is None
    assert provider.get_installed_models() == []
    assert provider.get_running_models() == []

    h = provider.health()
    assert h.status == "Offline"
