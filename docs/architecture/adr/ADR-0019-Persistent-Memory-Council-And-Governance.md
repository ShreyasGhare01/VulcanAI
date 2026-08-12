# ADR-0019: Persistent Memory Council & Governance

## Status
Accepted

## Date
2025-02-15

## Authors
Jules & Vulcan Core Team

---

## Context
In early AI conversational agents, memory is often conflated with dialogue history, causing agents to be either stateless or overwhelmed by long, repetitive chat logs. Such systems prune historical logs arbitrarily and struggle with recall accuracy, data privacy, duplication, and transparency.

Vulcan requires a structured, persistent, and multi-domain memory subsystem. This subsystem must support:
1. Complete separation of temporary task/dialogue concerns from permanent user/world knowledge.
2. Direct, transparent human inspection using a human-readable Obsidian Markdown vault.
3. Decoupling of memory processing into high-integrity pipeline stages (Extraction, Classification, Validation, Consolidation).
4. Strong semantic indexing alongside structured metadata tracking.

## Decision
We implement a **Persistent Memory Architecture** consisting of six separate memory interfaces governed by a central **Memory Council** and regulated by a dedicated **Memory Governance** component.

Memory storage responsibilities are structured in complementary layers:
- **Obsidian (Knowledge Vault)**: Markdown files with standard YAML Frontmatter represent the absolute source of truth for human and machine knowledge.
- **SQLite Database**: Serves as the catalog, indexing YAML frontmatter UUIDs, paths, metadata (confidence, importance, version), relationship graph links, and the autobiographical Life Log.
- **ChromaDB**: Holds semantic vector embeddings corresponding to Obsidian blocks and files for similarity lookup.

We introduce two architectural components to coordinate these:
1. **Memory Council**: Evaluates when dialogue should become a permanent memory, handles queueing for offline extraction when Ollama is offline, and coordinates the extractive pipeline.
2. **Memory Governance**: Decouples deduplication, version conflict resolutions, and privacy rules (e.g. blocking credentials or SSNs) from the general storage layer.

## Alternatives Considered
- *Using SQLAlchemy/ORMs for SQLite*: Rejected to preserve the engineering principle of direct standard `sqlite3` usage without external heavy-weight dependencies.
- *Saving flat text files instead of standard Markdown with YAML*: Rejected because standard Markdown with YAML Frontmatter maximizes the compatibility with Obsidian vaults.

## Consequences
- **Easier Auditability**: Users can inspect and edit their memories directly by pointing an Obsidian application at their local vault.
- **Improved Performance**: The UI thread never blocks on vector operations or LLM calls; the Memory Council safely manages offline retry queues when models are offline.
- **Clean Separation**: Identity memory (Constitution/skills) is completely isolated from user knowledge.

## Tradeoffs
- **Redundancy**: Maintaining metadata in SQLite, vectors in ChromaDB, and source content in Obsidian introduces synchronicity complexity.

## Future Evolution
1. **Human-in-the-Loop Interception**: The Memory Council's candidates can easily be routed to a PySide6 GUI panel, letting users approve, modify, or delete a fact before it is written to the vault.
2. **Cross-Agent Memory Synclink**: In future multi-agent phases, specialized agent personas can be assigned subdirectories inside the Obsidian vault (e.g., `obsidian_vault/Agents/DevAgent/`) allowing them to share or limit domain context.
3. **Decade-scale Semantic Pruning**: Low-importance or stale SQLite metadata can be flagged for automated archiving to save vector space.

## Related ADRs
- ADR-0006: SQLite Data Layer
- ADR-0007: ChromaDB Abstraction
- ADR-0012: Memory Separation

## References
- `vulcan/memory/`
- `docs/architecture/Memory_Architecture_Specification.md`
