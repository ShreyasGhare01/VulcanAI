# ADR-0007: ChromaDB Abstraction

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
We need a local vector database to store document embeddings, user conversations, and semantic facts for Knowledge Memory retrieval. However, ChromaDB can sometimes fail to install or compile on certain operating systems or older environments, which could prevent Vulcan from starting.

### Decision
We wrap ChromaDB inside a fully typed service abstraction wrapper (`ChromaService` in `vulcan/services/chroma.py`). The service must gracefully handle environments where ChromaDB is unavailable, allowing Vulcan to boot cleanly by failing gracefully without crashing.

### Alternatives Considered
*   **FAISS / Milvus / Qdrant**: Either too complex to install locally (requiring docker containers) or lack simple, lightweight embedded python client APIs like Chroma.
*   **In-Memory Dict Search**: Used strictly as the fallback mechanism if ChromaDB fails to load.

### Consequences
*   **Easier**: Clean, local-first vector embeddings storage with instant query capabilities.
*   **Harder**: Requires writing defensive `try-except` try-loads and mock fallback strategies inside `vulcan/services/chroma.py`.

### Tradeoffs
We select ChromaDB for its ease of use and local persistence, but write a custom wrapper to safeguard system execution if native compilation issues occur on some user platforms.

### Future Considerations
We can swap ChromaDB for PGVector or a remote Qdrant service simply by implementing the corresponding domain interface, preserving complete system replaceability.

### Related ADRs
*   ADR-0012: Memory Separation

### References
*   `vulcan/services/chroma.py`
