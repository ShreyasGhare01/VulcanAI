# ADR-0012: User Memory vs AI Memory Separation

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
In AI projects, memory is often treated as a single monolith (e.g., throwing all data into a vector database). However, an operating system needs to distinguish between volatile session context, structural system information, and the user's personal, human-written knowledge base.

### Decision
We partition the memory architecture into seven distinct, non-overlapping domains coordinated by an abstract `IMemoryManager`:
1.  **Working Memory**: Volatile active task tracking.
2.  **Identity Memory**: Core configurations and system personality.
3.  **Experience Memory**: Chronological action and communication logs.
4.  **Knowledge Memory**: Semantic facts stored as vector embeddings.
5.  **Reflection Memory**: Synthesized summaries and performance feedback loops.
6.  **Development Memory**: Workspace code structure.
7.  **User Memory**: An Obsidian-backed knowledge vault represented by a dedicated interface (`IUserMemory`).

**Rule**: Vulcan can interface with the Obsidian vault but must treat it as a read-first, highly controlled component. It must never freely reorganize, prune, or delete user-written notes.

### Alternatives Considered
*   **Monolithic Vector Search**: Simpler to write initially but makes session-level logic, security, and human-in-the-loop audit paths highly chaotic.

### Consequences
*   **Easier**: Clean, domain-isolated database tables. The user can easily back up their Obsidian vault without carrying internal AI session states.
*   **Harder**: Requires writing separate interface classes and data adapters for each memory subsystem.

### Tradeoffs
We prioritize memory safety, privacy, and system transparency over the initial convenience of a single database file.

### Future Considerations
We can configure different backends for each domain (e.g., in-memory for Working, SQLite for Experience, and Obsidian files for User).

### Related ADRs
*   ADR-0007: ChromaDB Abstraction
*   ADR-0013: Interface-First Development Philosophy

### References
*   `vulcan/memory/interfaces.py`
