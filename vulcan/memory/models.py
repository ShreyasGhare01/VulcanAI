"""Structured memory Pydantic models for extraction pipeline, metadata catalog, and retrieval."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MemoryRelationship(BaseModel):
    """Refers to a semantic relationship inside the knowledge model."""

    target_uuid: str = Field(description="The target memory record unique identifier.")
    relation: str = Field(description="Semantic link (e.g. 'Uses', 'Knows', 'Studies').")


class MemoryProvenance(BaseModel):
    """Traces where and why a memory was recorded."""

    origin: str = Field(
        default="conversation",
        description="Source type: e.g. 'conversation', 'imported_file', 'manual_edit', 'reflection'.",
    )
    conversation_session_id: str | None = Field(
        default=None, description="The session ID from which this fact was derived."
    )
    correlation_id: str | None = Field(
        default=None, description="Unique correlation execution ID for tracing."
    )
    extracted_by: str | None = Field(
        default=None, description="Identifier of the extraction provider/model."
    )


class MemoryCandidate(BaseModel):
    """Unified schema model for extracted memory candidates prior to storage and consolidated integration."""

    uuid: UUID = Field(default_factory=uuid4, description="The record unique identifier.")
    memory_type: str = Field(
        description="Memory scope type: e.g. 'working', 'conversation', 'knowledge', 'life_log', 'reflection', 'identity'."
    )
    category: str = Field(
        description="Factual domain label: e.g. 'fact', 'preference', 'goal', 'project', 'relationship', 'skill', 'schedule'."
    )
    title: str = Field(
        description="Human-readable summary title (e.g., 'Favorite IDE' or 'Education details')."
    )
    content: str = Field(description="Detailed fact context or markdown representation.")
    importance: str = Field(
        default="medium",
        description="Calculated importance tier: e.g. 'critical', 'high', 'medium', 'low', 'ignore'.",
    )
    confidence: float = Field(
        default=0.9, description="Confidence assessment score from 0.0 to 1.0."
    )
    relationships: list[MemoryRelationship] = Field(
        default_factory=list, description="Associated conceptual entity links."
    )
    provenance: MemoryProvenance = Field(
        default_factory=MemoryProvenance, description="Origin tracing metadata."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Factual record creation timestamp."
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Factual record update timestamp."
    )
    version: int = Field(default=1, description="Sequential revision catalog version.")
    tags: list[str] = Field(default_factory=list, description="Categorization keywords.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary extension parameters."
    )


class RetrievalResult(BaseModel):
    """Result of multi-dimensional recall scoring."""

    candidate: MemoryCandidate
    score: float
    reasoning: str | None = None
