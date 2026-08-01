"""Strongly-typed Pydantic domain models for Vulcan AI OS."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class HealthState(StrEnum):
    """Supported service lifecycle health states."""

    ONLINE = "Online"
    OFFLINE = "Offline"
    DEGRADED = "Degraded"
    INITIALIZING = "Initializing"
    STOPPING = "Stopping"


class HealthStatus(BaseModel):
    """Service health state reporting container."""

    status: HealthState
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class SkillManifest(BaseModel):
    """Pydantic validation schema for Skill manifests."""

    manifest_version: int = 1
    name: str
    version: str
    author: str
    description: str
    required_permissions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    exposed_capabilities: list[str] = Field(default_factory=list)
    minimum_vulcan_version: str = "0.1.0"


class CapabilityStability(StrEnum):
    """Stability flag for registered capabilities."""

    EXPERIMENTAL = "Experimental"
    STABLE = "Stable"
    DEPRECATED = "Deprecated"


class Capability(BaseModel):
    """Metadata representing a registered capability."""

    name: str
    version: str = "0.1.0"
    description: str
    provider: str
    required_permissions: list[str] = Field(default_factory=list)
    stability: CapabilityStability = CapabilityStability.STABLE
    tags: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    """Model information descriptor."""

    name: str
    version: str | None = None
    size_bytes: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AgentInfo(BaseModel):
    """Agent runtime descriptor metadata."""

    agent_id: str
    role: str
    status: str
    capabilities: list[str] = Field(default_factory=list)


class TaskInfo(BaseModel):
    """Task metadata descriptor."""

    id: str
    name: str
    status: str
    assigned_agent: str | None = None
