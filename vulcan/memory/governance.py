"""Memory Governance layer regulating retention, duplicates, conflicts, and privacy."""

from vulcan.memory.models import MemoryCandidate
from vulcan.memory.sqlite_store import SQLiteRepository
from vulcan.utils.logging import get_logger


from enum import StrEnum


class PrivacyCategory(StrEnum):
    """Extensible privacy classifications."""

    PUBLIC = "PUBLIC"
    PERSONAL = "PERSONAL"
    SENSITIVE = "SENSITIVE"
    RESTRICTED = "RESTRICTED"
    NEVER_STORE = "NEVER_STORE"


class MemoryGovernance:
    """The safety and consistency conscience regulating Vulcan memory operations."""

    def __init__(self, sqlite_repo: SQLiteRepository):
        self.sqlite_repo = sqlite_repo
        self.logger = get_logger("memory_governance")

        # Extensible default categories and rules
        self.privacy_categories: dict[str, PrivacyCategory] = {
            "public": PrivacyCategory.PUBLIC,
            "personal": PrivacyCategory.PERSONAL,
            "sensitive": PrivacyCategory.SENSITIVE,
            "restricted": PrivacyCategory.RESTRICTED,
            "never_store": PrivacyCategory.NEVER_STORE,
        }

    def determine_privacy_category(self, candidate: MemoryCandidate) -> PrivacyCategory:
        """Heuristically determines the privacy categorization of an incoming memory."""
        content_lower = candidate.content.lower().strip()
        sensitive_keywords = [
            "password:",
            "ssn:",
            "api_key:",
            "api-key:",
            "private_key:",
            "credentials:",
        ]
        personal_keywords = [
            "birthday",
            "spouse",
            "child",
            "wife",
            "husband",
            "family",
            "address",
            "phone",
        ]

        if any(kw in content_lower for kw in sensitive_keywords):
            return PrivacyCategory.NEVER_STORE
        elif any(kw in content_lower for kw in personal_keywords):
            return PrivacyCategory.PERSONAL
        return PrivacyCategory.PUBLIC

    def approve_storage(self, candidate: MemoryCandidate) -> bool:
        """Determines if a memory complies with privacy policies and should be saved."""
        content_lower = candidate.content.lower().strip()

        # 1. Enforce privacy classifications
        category = self.determine_privacy_category(candidate)
        if category == PrivacyCategory.NEVER_STORE:
            self.logger.warning(
                f"Memory Governance BLOCKED storage of candidate '{candidate.title}': Restricted NEVER_STORE category detected."
            )
            return False

        if len(content_lower) < 3:
            self.logger.info(
                f"Memory Governance BLOCKED candidate '{candidate.title}': Content is too short."
            )
            return False

        return True

    def resolve_conflicts(self, candidate: MemoryCandidate) -> MemoryCandidate | None:
        """Applies conflict resolution policies (e.g. archiving older contradicting values)."""
        # Look up similar categories/titles in SQLite catalog
        matches = self.sqlite_repo.list_catalog(
            {"category": candidate.category, "title": candidate.title}
        )
        if matches:
            # We have a conflict/update.
            latest_match = max(matches, key=lambda m: m["version"])
            if latest_match["version"] >= candidate.version:
                # Increment incoming version to exceed catalog
                candidate.version = latest_match["version"] + 1

            self.logger.info(
                f"Memory Governance resolved update version conflict for '{candidate.title}': Set to version {candidate.version}"
            )

        return candidate

    def detect_duplicates(self, candidate: MemoryCandidate) -> bool:
        """Determines if an exact semantic duplicate exists in SQLite catalog."""
        matches = self.sqlite_repo.list_catalog(
            {"category": candidate.category, "title": candidate.title}
        )
        for m in matches:
            # Reconstruct content/value logic or check simple existence
            if m["confidence"] >= candidate.confidence and m["version"] >= candidate.version:
                # We have a newer or higher confidence identical entry
                return True
        return False
