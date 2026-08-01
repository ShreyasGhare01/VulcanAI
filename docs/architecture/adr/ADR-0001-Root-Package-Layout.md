# ADR-0001: Root Package Layout

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
In previous AI and operating system projects, the codebase structure often became cluttered, making it difficult to find source files and causing import path conflicts (e.g., conflicting with local script execution or system-wide libraries). We need a clear, professional, and standard repository organization that scales as Vulcan grows.

### Decision
We will enforce a single root package layout named `vulcan` located at the root of the repository. All application subpackages (e.g., config, core, UI, memory) must reside within this folder. No executable scripts should be placed directly in the repository root other than typical configuration files (such as `pyproject.toml`). All imports must use the absolute `vulcan` namespace (e.g., `from vulcan.core.event_bus import EventBus`).

### Alternatives Considered
*   **Src-based Layout (`src/vulcan/`)**: While this is a standard Python packaging layout, we chose a single root package layout to minimize import nesting and streamline local development and testing.
*   **Flat Root Layout**: Placing modules directly in the root directory. This was rejected because it scatters Python files among repository configuration files, making packaging and distribution messy.

### Consequences
*   **Easier**: Clean packaging using Poetry/setuptools, clear separation between test suites (`tests/`) and application logic, and consistent absolute imports.
*   **Harder**: Running tools requires setting `PYTHONPATH=.` or installing the package in editable mode (`pip install -e .`).

### Tradeoffs
We prioritize clean namespace isolation and packaging structure over the ease of running uninstalled scripts via direct file executions.

### Future Considerations
If Vulcan is distributed as a system service or binary, this layout simplifies compilation and path resolution.

### Related ADRs
*   None

### References
*   `vulcan/` root directory
*   `pyproject.toml`
