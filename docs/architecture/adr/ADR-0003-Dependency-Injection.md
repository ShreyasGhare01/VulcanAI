# ADR-0003: Dependency Injection / Service Container

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
In complex modular applications, hardcoding class instances inside consumers makes testing very difficult. We need a way to manage long-lived service lifecycles (initialize, start, stop, shutdown) and resolve dependencies cleanly at application startup.

### Decision
We implement a lightweight `IServiceContainer` and concrete `ServiceContainer` (in `vulcan/core/container.py`) to serve as our dependency injection system. The container holds registrations of abstract interfaces to concrete instances. The application bootstrapping phase (`Bootstrapper` in `vulcan/core/bootstrap.py`) registers the core services into the container.

### Alternatives Considered
*   **Global Singletons**: Easy to write but tightly couples components, making test parallelization and mock injection extremely difficult.
*   **Third-party DI Frameworks (e.g., dependency-injector)**: Rejected to keep the core OS code lightweight and free from complex third-party setup dependencies.

### Consequences
*   **Easier**: We can replace any real service (like `OllamaProvider`) with a mocked instance during testing by simply registering the mock in the test container.
*   **Harder**: Requires passing the container or dependencies during bootstrapping, though this is minimized by preferring constructor injection in business logic.

### Tradeoffs
Implementing a custom container requires minimal code (around 30 lines) but gives us complete, lightweight control over dependency mappings and lifetimes.

### Future Considerations
The container structure naturally supports scaling up to automatic constructor resolution if necessary in later phases.

### Related ADRs
*   ADR-0014: Constructor Injection Preference

### References
*   `vulcan/core/container.py`
*   `vulcan/core/bootstrap.py`
