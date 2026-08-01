import pytest
import json
from typing import Any
from vulcan.core.registry import CapabilityRegistry
from vulcan.core.skills_loader import SkillLoader


def test_skills_loader_isolation_and_validation(tmp_path: Any) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create a valid skill pack
    skill_valid = skills_dir / "filesystem"
    skill_valid.mkdir()
    manifest_valid = {
        "manifest_version": 1,
        "name": "filesystem",
        "version": "1.0.0",
        "author": "Core",
        "description": "Valid Pack",
        "exposed_capabilities": ["filesystem.read"],
    }
    with open(skill_valid / "manifest.json", "w") as f:
        json.dump(manifest_valid, f)

    # Create an invalid skill pack (unsupported/low manifest_version)
    skill_invalid_version = skills_dir / "old_skill"
    skill_invalid_version.mkdir()
    manifest_invalid = {
        "manifest_version": 0,  # Invalid version!
        "name": "old_skill",
        "version": "0.1.0",
        "author": "Legacy",
        "description": "Invalid manifest version",
        "exposed_capabilities": ["legacy.run"],
    }
    with open(skill_invalid_version / "manifest.json", "w") as f:
        json.dump(manifest_invalid, f)

    # Run the loader and verify failure isolation
    registry = CapabilityRegistry()
    loader = SkillLoader(registry=registry, skills_dir=str(skills_dir))
    discovered = loader.discover_and_register_all()

    # The loader should skip 'old_skill' but successfully load 'filesystem'
    assert len(discovered) == 1
    assert discovered[0].name == "filesystem"
    assert registry.has_capability("filesystem.read")
    assert not registry.has_capability("legacy.run")
