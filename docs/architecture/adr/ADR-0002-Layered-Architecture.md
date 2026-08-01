# ADR-0002: Layered Architecture

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
Without clear boundaries, complex software applications can suffer from "spaghetti code," where UI widgets directly make database queries or orchestrate agent tasks. This makes the system brittle, difficult to test, and impossible to port to other interfaces (e.g., CLI or web).

### Decision
We establish a strict four-layer architecture with a downward/inward dependency flow rule:
1.  **Presentation Layer** (PySide6 UI, CLI)
2.  **Orchestration Layer** (Planners, Task execution, Command routing)
3.  **Domain Layer** (Pure Python, interfaces, business rules)
4.  **Infrastructure Layer** (OllamaProvider, SQLite, ChromaDB)

**Inward Flow Rule**: Lower layers must never import or depend on symbols from higher layers (e.g., no imports of `PySide6` or UI widgets inside `vulcan/core/` or `vulcan/services/`).

### Alternatives Considered
*   **Monolithic Model-View-Controller (MVC)**: Rejected because MVC does not provide sufficient separation of concerns for complex AI planners and local background executors.
*   **Clean Architecture (Hexagonal / Ports-and-Adapters)**: Fully adopted and adapted here as our inward-flowing four-layer structure.

### Consequences
*   **Easier**: We can mock infrastructure databases and models for unit tests, reuse domain logic across UI/CLI interfaces, and easily replace components.
*   **Harder**: Requires creating boilerplate interfaces (`abc.ABC`) and data models before writing any concrete code.

### Tradeoffs
We accept the minor overhead of defining interfaces in the Domain layer to guarantee high maintainability and clean boundaries.

### Future Considerations
This design makes it possible to completely replace PySide6 with a web-based dashboard in future versions without rewriting any core AI or file execution code.

### Related ADRs
*   None

### References
*   `docs/architecture/Layer_Rules.md`
