"""Custom error and exception hierarchy for the Vulcan AI OS."""


class VulcanError(Exception):
    """Base exception for all errors inside Vulcan."""

    pass


class ConfigurationError(VulcanError):
    """Raised when there are configuration loading or validation failures."""

    pass


class PluginError(VulcanError):
    """Raised during third-party plugin installation or loading issues."""

    pass


class SkillError(VulcanError):
    """Raised during skill validation, packaging, or execution anomalies."""

    pass


class MemoryError(VulcanError):
    """Raised when underlying memory interfaces or persistent transactions fail."""

    pass


class ModelError(VulcanError):
    """Raised when LLM/Inference endpoints fail or are completely offline."""

    pass


class AgentError(VulcanError):
    """Raised during task scheduling or agent plan execution failures."""

    pass


class UIError(VulcanError):
    """Raised when visual or layout elements run into rendering problems."""

    pass
