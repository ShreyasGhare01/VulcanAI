"""Persistent system identity assembler."""

from typing import Any

from pydantic import BaseModel, Field


class SystemIdentity(BaseModel):
    """The structured data container representing Vulcan's identity."""

    name: str = "Vulcan"
    constitution_summary: str = Field(
        default="I serve to augment human capability while preserving user control, privacy, and absolute transparency."
    )
    operating_rules: list[str] = Field(
        default_factory=lambda: [
            "UI thread coordinates exclusively with visual rendering.",
            "Long-running tasks run in dedicated background workers.",
            "Maintain absolute local-first independence.",
            "No hidden executions or file modifications outside the workspace.",
        ]
    )
    preferences: dict[str, Any] = Field(default_factory=dict)


class IdentityProvider:
    """Assembles the immutable system identity from Constitution and Config."""

    def __init__(self, config: Any):
        self.config = config

    def assemble_identity(self) -> SystemIdentity:
        """Constructs and returns structured SystemIdentity data."""
        # Derived from Constitution and VAS
        return SystemIdentity(
            name=self.config.app.name,
            constitution_summary=(
                "Vulcan is an open, coherent, and modular AI Operating System. "
                "The user remains the sovereign authority. "
                "The user has the Right to Ultimate Control, Absolute Privacy, Clear Explanation, and Reversibility. "
                "Under no circumstances shall the agent silently destroy or rewrite the user's external personal knowledge base."
            ),
            operating_rules=[
                "Separation of concerns: presentation logic must remain thin.",
                "The UI thread must never run blocking network, LLM, or vector search queries.",
                "Every major subsystem is defined behind a clean interface.",
                "Operate strictly within local-first limits and sandbox workspace boundaries.",
                "Write structured records of plans and capability executions to the Life Log.",
            ],
            preferences={
                "environment": self.config.app.environment,
                "workspace_dir": self.config.app.workspace_dir,
            },
        )
