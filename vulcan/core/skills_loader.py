"""Auto-discovery dynamic skills loader scanning folders for manifest.json with constructor injection."""

import json
import os

from pydantic import ValidationError

from vulcan.core.models import Capability, SkillManifest
from vulcan.core.registry import ICapabilityRegistry
from vulcan.utils.logging import get_logger


class SkillLoader:
    """Discovers and registers local skills based on workspace folder scanning."""

    def __init__(self, registry: ICapabilityRegistry, skills_dir: str = "./vulcan/skills"):
        self.registry = registry
        self.skills_dir = skills_dir
        self.logger = get_logger("skill_loader")

    def discover_and_register_all(self) -> list[SkillManifest]:
        """Scans skills directory, parses/validates manifest schemas, and registers capabilities."""
        discovered: list[SkillManifest] = []
        if not os.path.exists(self.skills_dir):
            self.logger.warning(f"Skills directory '{self.skills_dir}' does not exist.")
            return discovered

        for entry in os.listdir(self.skills_dir):
            subpath = os.path.join(self.skills_dir, entry)
            if os.path.isdir(subpath):
                manifest_path = os.path.join(subpath, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path) as f:
                            raw_data = json.load(f)

                        # Validate manifest schema cleanly using Pydantic
                        manifest = SkillManifest.model_validate(raw_data)

                        # Isolate failure if manifest version is invalid/unsupported
                        if manifest.manifest_version < 1:
                            self.logger.error(
                                f"Skill '{manifest.name}' has invalid manifest_version: {manifest.manifest_version}"
                            )
                            continue

                        self.logger.info(
                            f"Discovered skill pack '{manifest.name}' (v{manifest.version})"
                        )

                        # Map and register all declared capabilities
                        for cap_name in manifest.exposed_capabilities:
                            cap_model = Capability(
                                name=cap_name,
                                version=manifest.version,
                                description=manifest.description,
                                provider=manifest.name,
                                required_permissions=manifest.required_permissions,
                            )
                            self.registry.register_capability(cap_model)

                        discovered.append(manifest)
                    except ValidationError as ve:
                        self.logger.error(
                            f"Schema validation failed for skill manifest at {manifest_path}: {ve}"
                        )
                    except Exception as e:
                        self.logger.error(f"Error loading skill manifest at {manifest_path}: {e}")

        return discovered
