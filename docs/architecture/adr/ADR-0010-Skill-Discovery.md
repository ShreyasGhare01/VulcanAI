# ADR-0010: Directory-Based Skill Discovery

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
We want an easy, modular way to add first-party capabilities (like workspace file access) and allow users to install third-party capabilities. We need a discovery strategy that avoids complex Python entrypoint registration.

### Decision
We implement a dynamic `SkillsLoader` (in `vulcan/core/skills_loader.py`) that scans the `vulcan/skills/` directory at startup.
*   Every skill must exist as its own subdirectory containing a `manifest.json` file.
*   The loader validates the manifest against a Pydantic `SkillManifest` model (enforcing `manifest_version >= 1`).
*   It registers exposed capabilities directly in the `CapabilityRegistry`.

### Alternatives Considered
*   **Python Entry Points (setuptools)**: Highly robust but requires compiling, installing, and managing pip packages for every added skill, complicating simple development.
*   **Hardcoded Skill Lists**: Highly rigid and prevents dynamic runtime addition of capabilities.

### Consequences
*   **Easier**: Installing a new skill is as simple as copying its directory into `vulcan/skills/`.
*   **Harder**: Requires writing defensive scanning, import, and Pydantic validation logic inside the `SkillsLoader`.

### Tradeoffs
We accept the minor performance scanning overhead at startup in exchange for incredibly simple file-drop skill installations.

### Future Considerations
We can expand this to support loading Skills from a custom `plugins/` folder to separate first-party and third-party extensions.

### Related ADRs
*   ADR-0005: Capability Registry
*   ADR-0011: Plugin Architecture

### References
*   `vulcan/core/skills_loader.py`
*   `vulcan/core/models.py` (SkillManifest)
