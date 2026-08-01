# ADR-0004: Event Bus

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
To keep subsystems decoupled and prevent UI code from blocking on background tasks, we need a robust, event-driven communication backbone. If a background model begins loading or a capability completes, interested observers need to react without the publisher needing to know who they are.

### Decision
We implement a central `EventBus` (conforming to `IEventBus` in `vulcan/core/event_bus.py`) as the asynchronous communication backbone.
*   **Hierarchical Namespaces**: Events are identified using a dot-notation pattern (e.g., `System.Started`, `Memory.Stored`).
*   **Pattern Matching**: Observers can subscribe to specific events or broad categories using wildcard matching (e.g., `System.*` matches all events starting with `System.`).

### Alternatives Considered
*   **Qt Signals**: Highly robust but tightly couples the system to PySide6/Qt libraries, violating our Layer Rules (non-UI packages importing Qt symbols).
*   **Direct Callbacks**: Brittle and tightly couples components together.

### Consequences
*   **Easier**: Fully decoupled notification flow. A skill can publish `Skill.File.Deleted` and the UI or audit logs can update without the skill having direct access to them.
*   **Harder**: Event flows can be harder to trace compared to sequential direct method calls. This is addressed by rigorous logging of event dispatches.

### Tradeoffs
We accept the trade-off of slightly reduced visual step-debugging clarity in exchange for complete horizontal decoupling and robust multi-threading safety.

### Future Considerations
We can bridge our custom event bus with a Qt Signal bridge inside the Presentation layer, allowing the UI to react safely on its GUI thread to background system events.

### Related ADRs
*   ADR-0002: Layered Architecture

### References
*   `vulcan/core/event_bus.py`
