"""Custom exception hierarchy representing Vulcan AI Operating System failures."""


class VulcanError(Exception):
    """Base exception for all Vulcan OS runtime and logical failures."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConfigurationError(VulcanError):
    """Raised when configuration values are missing, invalid, or corrupted."""

    pass


class PluginError(VulcanError):
    """Raised when third-party plugin loading or capability execution fails."""

    pass


class SkillError(VulcanError):
    """Raised when skill manifests, tools, or registrations fail validation."""

    pass


class MemoryError(VulcanError):
    """Raised when memory transactions, vector retrieval, or pipeline validations fail."""

    pass


class ModelError(VulcanError):
    """Raised when model inference endpoints are unreachable or parameters are rejected."""

    pass


class AgentError(VulcanError):
    """Raised when agent workflows, planners, or lifecycle transitions fail."""

    pass


class UIError(VulcanError):
    """Raised when presentation layer, Qt workers, or panel layout persists fail."""

    pass
