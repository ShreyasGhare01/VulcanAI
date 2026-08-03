"""Infrastructure Services Subsystem package.

Responsibility:
    Responsible for concrete integrations with local databases (SQLite), vector databases
    (ChromaDB), and local/offline language model inference servers (OllamaProvider).

Dependencies:
    - vulcan/config/ (VulcanConfig)
    - external database drivers and HTTP clients (httpx, sqlite3, chromadb)

Public Interfaces:
    - IInferenceProvider, OllamaProvider
    - IChromaService, ChromaService

Forbidden Dependencies:
    - No presentation layers or UI widgets (vulcan/ui/) may be imported here.
    - No direct business logic or conversational loop orchestration (vulcan/cognition/).
"""
