# ADR-0013: Interface-First Development Philosophy

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
To prevent circular imports, decouple vertical layers, and enable robust mocking, we need a consistent way to define services before implementing their concrete logic.

### Decision
We establish a strict naming convention and development rule:
*   Every major service must first define an abstract base class (interface) prefixed with `I` (e.g., `IEventBus`, `IInferenceProvider`, `IUserMemory`).
*   Concrete implementations must have clean names without prefixes (e.g., `EventBus`, `OllamaProvider`, `ObsidianUserMemory`).
*   The codebase must strictly import and type-annotate using the interfaces (prefixed with `I`), resolving implementations at runtime via dependency injection.

### Alternatives Considered
*   **Concrete-First Development**: Writing classes directly. This is common in simple scripts but quickly leads to tight coupling and makes unit testing databases and network calls extremely difficult.

### Consequences
*   **Easier**: Clean decoupling. We can run our entire test suite without spinning up an Ollama server or initializing a Chroma database because we can mock their interfaces instantly.
*   **Harder**: Requires maintaining two classes (the interface and the implementation) for each core service.

### Tradeoffs
We accept the minor overhead of managing interfaces to guarantee excellent testability, clean code boundaries, and modularity.

### Future Considerations
This ensures that any future developer or AI agent (like Jules) can instantly understand a service's public contract by reading its interface definition without getting lost in implementation details.

### Related ADRs
*   ADR-0002: Layered Architecture
*   ADR-0003: Dependency Injection

### References
*   `vulcan/memory/interfaces.py`
*   `vulcan/services/inference.py` (IInferenceProvider)
