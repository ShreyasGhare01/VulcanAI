# ADR-0005: Capability Registry

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
In an extensible AI OS, agents need to discover and invoke tools, services, and tasks dynamically. Hardcoding direct implementation calls makes the agent framework highly rigid and limits third-party skill packs from introducing new capabilities.

### Decision
We implement a thread-safe `CapabilityRegistry` (conforming to `ICapabilityRegistry` in `vulcan/core/registry.py`).
*   **Decoupled Routing**: Subsystems register their functional capabilities (represented as a strongly typed Pydantic `Capability` containing schemas, stability ratings, and permission definitions).
*   **Dynamic Resolution**: Consuming components query the registry dynamically using strings (e.g., `filesystem.read`) to resolve the provider.

### Alternatives Considered
*   **Direct Method Invocation**: Standard but does not support dynamic discovery by AI planners.
*   **Global Tool Map**: Less structured; does not enforce version checking, permissions, or input/output schema validation.

### Consequences
*   **Easier**: Clean, schema-validated routing of actions. Agents can query the registry to find out which capabilities are available on startup.
*   **Harder**: Requires defining strict metadata schemas and registering each capability during the bootstrap phase.

### Tradeoffs
The registry adds a small layer of overhead but is critical to establishing a secure, pluggable capability system.

### Future Considerations
The registry will eventually act as the gatekeeper for user capability authorization (checking if a skill has permission to execute a capability).

### Related ADRs
*   ADR-0010: Skill Discovery

### References
*   `vulcan/core/registry.py`
*   `vulcan/core/models.py`
