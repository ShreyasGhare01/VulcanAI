# ADR-0011: Plugin Architecture

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
We need to clearly distinguish first-party core skills from third-party extensions. If we lump all third-party integrations into the primary codebase, the repository will suffer from dependency sprawl and become highly fragile.

### Decision
We establish a structural split:
*   **Skills**: First-party core capabilities located under `vulcan/skills/` (such as local workspace file access).
*   **Plugins**: Third-party extensions located under `vulcan/plugins/`. Plugins will be loaded dynamically, scanning directories for a specific manifest file rather than using Python entry points.

### Alternatives Considered
*   **Monolithic Integration**: Putting all extensions in a single folder. This was rejected because it violates the separation of concerns and complicates the core system licensing, security, and updates.

### Consequences
*   **Easier**: The core OS remains lightweight, stable, and highly secure.
*   **Harder**: Requires maintaining two separate loading mechanisms (though they can share underlying manifest validation utilities).

### Tradeoffs
Separating skills and plugins introduces two layout locations but ensures clean boundary guidelines for developers.

### Future Considerations
We can implement an extension dashboard in the UI allowing users to easily enable or disable loaded plugins.

### Related ADRs
*   ADR-0010: Skill Discovery

### References
*   `docs/architecture/Vulcan_Architecture_Specification.md` (Plugin System section)
