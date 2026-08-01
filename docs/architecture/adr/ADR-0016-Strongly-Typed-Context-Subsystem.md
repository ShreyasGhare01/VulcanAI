# ADR-0016: Strongly-Typed Context Subsystem

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
In AI-native architectures, "context" represents the active environmental state, limits, profiles, and scopes passed between prompt compilers, LLM interfaces, and agent planners. Using untyped Python dictionaries (`dict[str, Any]`) to manage this state leads to fragile code, missing keys, hard-to-trace bugs, and poor self-documentation.

### Decision
We introduce a dedicated, strongly-typed Context layer under `vulcan/core/context.py` using Pydantic `BaseModel` classes:
1.  **ConversationContext**: Session IDs, message timestamps, active tokens, and metadata.
2.  **TaskContext**: Hierarchical task tracking, deadlines, priorities, and variable mappings.
3.  **ExecutionContext**: OS environment scopes, workspace constraints, and loaded capabilities.
4.  **AgentContext**: Persona setups, temperature settings, budget boundaries, and goals.
5.  **MemoryContext**: Search limits, similarity thresholds, and scratchpads.

### Alternatives Considered
*   **Raw Dictionaries**: Flexible but lacks validation, standard autocomplete support, and compile-time/static type checking.
*   **Dynamic dataclasses**: Lacks the serialization, validation, and JSON schema-generation benefits that Pydantic models natively provide.

### Consequences
*   **Easier**: Guaranteed field validation, robust self-documentation, static type check compliance (Mypy/Ruff), and simple serialization to system logs or databases.
*   **Harder**: Requires instantiating concrete Pydantic context objects instead of passing raw dict literals.

### Tradeoffs
We prioritize type-safety, contract enforcement, and robust auditing over the absolute flexibility of raw key-value dictionary passing.

### Future Considerations
These models make it incredibly straightforward to dynamically serialize and deserialize active execution and task contexts to relational databases (SQLite) or transmit them across API endpoints in future multi-agent or remote client versions of Vulcan.

### Related ADRs
*   ADR-0002: Layered Architecture
*   ADR-0012: Memory Separation

### References
*   `vulcan/core/context.py`
*   `tests/test_context.py`
