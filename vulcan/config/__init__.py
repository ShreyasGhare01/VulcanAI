"""Configuration models and loading mechanics for Vulcan AI OS."""

import json
import os
from typing import Any, Dict, Optional


class AppConfig:
    """General application settings."""

    def __init__(self) -> None:
        self.name: str = "Vulcan AI Operating System"
        self.version: str = "0.1.0"
        self.debug: bool = False
        self.environment: str = "production"
        self.workspace_dir: str = "./vulcan/workspace"


class LoggingConfig:
    """Logging configuration settings."""

    def __init__(self) -> None:
        self.level: str = "INFO"
        self.log_to_file: bool = True
        self.log_file_path: str = "./logs/vulcan.log"
        self.rotation: str = "10 MB"
        self.retention: str = "1 week"
        self.structured: bool = True


class ModelConfig:
    """Model/Inference service configuration settings."""

    def __init__(self) -> None:
        self.ollama_url: str = "http://localhost:11434"
        self.default_model: str = "llama3:latest"
        self.temperature: float = 0.7
        self.timeout_seconds: int = 10


class UIConfig:
    """User Interface configuration settings."""

    def __init__(self) -> None:
        self.theme: str = "dark"
        self.width: int = 1200
        self.height: int = 800
        self.persist_layout: bool = True


class SQLiteConfig:
    """SQLite Database configuration settings."""

    def __init__(self, db_path: str = "./vulcan/workspace/vulcan.db") -> None:
        self.db_path: str = db_path
        self.timeout_seconds: int = 5


class ChromaConfig:
    """ChromaDB configuration settings."""

    def __init__(self, persist_directory: str = "./vulcan/workspace/chroma") -> None:
        self.persist_directory: str = persist_directory
        self.collection_name: str = "vulcan_memories"


class VulcanConfig:
    """Main layered configuration container for Vulcan AI OS."""

    def __init__(self) -> None:
        self.app = AppConfig()
        self.logging = LoggingConfig()
        self.model = ModelConfig()
        self.ui = UIConfig()
        self.sqlite = SQLiteConfig()
        self.chroma = ChromaConfig()


def load_config(
    config_dict: Optional[Dict[str, Any]] = None, config_filepath: Optional[str] = None
) -> VulcanConfig:
    """Loads configuration by resolving priorities:

    1. Defaults
    2. Configuration File (JSON/YAML/etc. - loaded here via dict)
    3. Environment Variables (prefixed with VULCAN_)
    4. Runtime overrides (via config_dict parameter)
    """
    config = VulcanConfig()

    # Load custom configuration from file if specified
    if config_filepath and os.path.exists(config_filepath):
        try:
            with open(config_filepath) as f:
                file_data = json.load(f)
                config = _overlay_dict(config, file_data)
        except Exception:
            pass

    # Apply runtime configurations override
    if config_dict:
        config = _overlay_dict(config, config_dict)

    return config


def _overlay_dict(config: VulcanConfig, overlay: Dict[str, Any]) -> VulcanConfig:
    """Helper to overlay standard nested dict onto the vulcan config."""
    for category, settings in overlay.items():
        if hasattr(config, category) and isinstance(settings, dict):
            target = getattr(config, category)
            for k, v in settings.items():
                if hasattr(target, k):
                    setattr(target, k, v)
        elif hasattr(config, category):
            setattr(config, category, settings)
    return config
