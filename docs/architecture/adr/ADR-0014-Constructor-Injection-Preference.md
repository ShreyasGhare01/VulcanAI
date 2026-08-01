# ADR-0014: Constructor Injection Preference

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
When using dependency injection containers, developers often use the Service Locator pattern, calling `container.resolve(IService)` directly inside business logic classes. This hides class dependencies, makes classes tightly coupled to the container itself, and complicates unit testing.

### Decision
We strictly prefer **Constructor Injection** over the Service Locator pattern.
*   Classes must declare their dependencies clearly in their `__init__` constructor methods (typed using interfaces).
*   The `ServiceContainer` should compose the application object graph during bootstrapping, rather than being passed around or called throughout business logic.

### Alternatives Considered
*   **Service Locator Pattern**: Resolving dependencies inside method calls using a global container instance. This was rejected because it conceals dependencies and makes tests dependent on initializing a global container state.

### Consequences
*   **Easier**: Clean, self-documenting code. You can instantiate any class in a test simply by passing standard Python objects or mocks directly to its constructor, with no container configuration required.
*   **Harder**: Bootstrapping files (like `vulcan/core/bootstrap.py`) become slightly more explicit as they coordinate and pass resolved dependencies to constructors.

### Tradeoffs
We prioritize transparent class dependencies and container-free testability over the magic of global service location.

### Future Considerations
This practice ensures our codebase remains standard Python, making it easy to migrate to other DI libraries or run code in alternative runtime environments if needed.

### Related ADRs
*   ADR-0003: Dependency Injection

### References
*   `vulcan/core/bootstrap.py`
