"""Extractive memory pipeline stages: Extractor, Classifier, Validator, and Consolidator."""

import json
from typing import Any

from vulcan.memory.models import MemoryCandidate, MemoryProvenance
from vulcan.services.inference import IInferenceProvider, InferenceRequest
from vulcan.utils.logging import get_logger


class MemoryExtractor:
    """Uses LLM to evaluate conversation turns and extract structured facts/candidates."""

    def __init__(
        self,
        inference_provider: IInferenceProvider,
        model_name: str,
        disable_thinking: bool = True,
    ):
        self.inference_provider = inference_provider
        self.model_name = model_name
        self.disable_thinking = disable_thinking
        self.logger = get_logger("memory_extractor")

    def extract_candidates(
        self,
        session_id: str,
        user_input: str,
        assistant_response: str,
        correlation_id: str | None = None,
    ) -> list[MemoryCandidate]:
        """Identifies if dialogue contains structured knowledge worth remembering.

        Raises ModelError when the model can't be reached, so the caller can keep the turn
        queued and retry later. A reply that isn't valid JSON is logged and treated as
        "nothing to remember", since retrying would most likely produce the same output.
        """

        prompt = f"""
        Analyze the following user-assistant turn to see if the user shared any permanent factual knowledge, preference, career goal, schedule, or project detail worth remembering.
        If yes, extract them as structured items. Ignore raw conversation filler, greetings, or short-lived statements (e.g. "I had pizza" or "thanks").

        User input: "{user_input}"
        Assistant response: "{assistant_response}"

        Return ONLY a JSON list of objects conforming to this schema:
        [
          {{
            "title": "Category/Subject name (e.g. 'Favorite IDE', 'Education')",
            "content": "The extracted factual statement(s)",
            "category": "One of: fact, preference, goal, project, relationship, skill, schedule"
          }}
        ]
        If nothing worth remembering was shared, return an empty list: []
        Do not include any Markdown wrapper, preamble or explanation. Output strict raw JSON.
        """

        req = InferenceRequest(
            model=self.model_name,
            system_prompt="You are Vulcan's Memory Extractor. You extract structured knowledge facts.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            think=False if self.disable_thinking else None,
        )
        # Let ModelError propagate: the turn must stay queued rather than be lost.
        response = self.inference_provider.generate(req)

        try:
            raw_text = response.assistant_message.strip()

            # Clean JSON markdown wrapper if LLM returned it
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```", 1)[1].rsplit("```", 1)[0].strip()

            if not raw_text or raw_text == "[]":
                return []

            items = json.loads(raw_text)
            candidates = []
            for item in items:
                prov = MemoryProvenance(
                    origin="conversation",
                    conversation_session_id=session_id,
                    correlation_id=correlation_id,
                )
                cand = MemoryCandidate(
                    memory_type="knowledge",
                    category=item.get("category", "fact"),
                    title=item.get("title", "Factual Memory"),
                    content=item.get("content", ""),
                    provenance=prov,
                )
                candidates.append(cand)
            return candidates
        except Exception as e:
            self.logger.error(f"Error during memory extraction: {e}")
            return []


class MemoryClassifier:
    """Validates and enforces canonical memory classifications."""

    def __init__(self) -> None:
        self.logger = get_logger("memory_classifier")

    def classify(self, candidate: MemoryCandidate) -> MemoryCandidate:
        """Enforces taxonomy boundaries on candidate type and category."""
        valid_categories = {
            "fact",
            "preference",
            "goal",
            "project",
            "relationship",
            "skill",
            "schedule",
            "reflection",
        }
        category_lower = candidate.category.lower().strip()
        if category_lower not in valid_categories:
            self.logger.info(f"Normalizing unrecognized category '{candidate.category}' to 'fact'")
            candidate.category = "fact"
        else:
            candidate.category = category_lower
        return candidate


class MemoryValidator:
    """Assigns memory importance and confidence scores based on phrasing and structures.

    Heuristic only: a model call per extracted fact is too slow on CPU-only hardware.
    """

    def __init__(self) -> None:
        self.logger = get_logger("memory_validator")

    def validate(self, candidate: MemoryCandidate) -> MemoryCandidate:
        """Calculates importance tier and confidence based on statements."""
        # Baseline heuristics
        content_lower = candidate.content.lower()

        # Confidence: check for tentative phrasing
        if any(
            w in content_lower for w in ["maybe", "think", "might", "possibly", "probably", "guess"]
        ):
            candidate.confidence = 0.60
        else:
            candidate.confidence = 0.95

        # Importance: Critical, High, Medium, Low, Ignore
        if any(
            w in content_lower for w in ["birthday", "spouse", "child", "wife", "husband", "family"]
        ):
            candidate.importance = "critical"
        elif any(
            w in content_lower for w in ["favorite ide", "major", "career", "programming language"]
        ):
            candidate.importance = "high"
        elif any(w in content_lower for w in ["pizza", "lunch", "weather", "today"]):
            candidate.importance = "ignore"
        else:
            candidate.importance = "medium"

        return candidate


class MemoryConsolidator:
    """Resolves duplications and merges incoming candidate statements into existing schemas."""

    def __init__(self, obsidian_vault: Any):
        self.obsidian_vault = obsidian_vault
        self.logger = get_logger("memory_consolidator")

    def consolidate(
        self, candidate: MemoryCandidate, existing_entries: list[MemoryCandidate]
    ) -> MemoryCandidate:
        """Merges duplicate facts, incrementing version numbers if content has changed."""
        for existing in existing_entries:
            # Check semantic match or title match
            if existing.title.lower().strip() == candidate.title.lower().strip():
                if existing.content.lower().strip() == candidate.content.lower().strip():
                    # Exact duplicate, mark to ignore or copy metadata
                    candidate.uuid = existing.uuid
                    candidate.version = existing.version
                    candidate.created_at = existing.created_at
                    return candidate
                else:
                    # Same title but different content -> Version Update
                    candidate.uuid = existing.uuid
                    candidate.version = (
                        existing.version + 1
                    )  # Will be written with incremented version
                    candidate.created_at = existing.created_at
                    return candidate
        return candidate
