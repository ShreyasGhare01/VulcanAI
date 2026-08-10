# Memory Architecture Specification (MAS)

**Version:** 1.0.0
**Applies to Vulcan Phase:** 2 Persistent Memory & Context
**Status:** Accepted
**Authors:** Jules & Vulcan Core Team
**Last Updated:** February 2025

---

## 1. Executive Summary

This document specifies the definitive design and operational architecture for the Vulcan AI Operating System's Persistent Memory Subsystem.

The biggest mistake conversational agents make is treating memory as flat, chronological dialogue history. Vulcan treats memory as **structured knowledge**, separate from dialogue. Dialogue is merely the staging area from which factual observations, system events, user preferences, and reflective patterns are extracted, classified, validated, consolidated, and persistently indexed.

---

## 2. Architectural Principles & Layout

The Persistent Memory system follows a strict layered architecture:

```
                  +-----------------------------------+
                  |          Memory Interfaces        | (IWorkingMemory, IConversationMemory, etc.)
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |       Memory Manager (Facade)     |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |      Memory Council / Pipeline    | (Extractor, Classifier, Validator, Consolidator)
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |         Storage Providers         | (SQLite, ChromaDB, Obsidian)
                  +-----------------------------------+
```

### 2.1 Storage Responsibilities

The storage backend utilizes three complementary technologies, each with a single, clear responsibility:

1.  **Obsidian (Knowledge Vault)**: Markdown documents. This is the **sacred, human-readable source of truth**. Vulcan never reorganizes or prunes this vault arbitrarily. The user can literally open their vault in Obsidian to read, edit, or audite everything Vulcan knows.
2.  **SQLite (Structural Index & Life Log)**: Keeps the catalog. Tracks relationships, metadata (UUIDs, timestamps, versions, confidence scores, importance metrics, file mappings), pending extraction queues, and the Life Log timeline.
3.  **ChromaDB (Semantic Search)**: Embeddings index for semantic vector searches. It holds semantic vector representations of Obsidian document blocks and headings for similarity lookup.

---

## 3. The Six Memory Subsystems

Vulcan maintains six completely separated memory subsystems, each designed for a different operational scope:

| Subsystem | Scope | Lifetime / Storage | Examples / Use Case |
| :--- | :--- | :--- | :--- |
| **Working Memory** | Temporary / Task-local | In-memory only (Never saved to Obsidian) | Active planner decisions, current command parameters, task context |
| **Conversation Memory** | Session-local Staging | Serialized in SQLite (Summarized over time) | Dialogue turns, message history, conversation tokens |
| **Long-Term Knowledge** | User & World facts | Obsidian Markdown (Vault) + SQLite Catalog + ChromaDB vectors | Favorite IDE, university name, project details, preferred writing styles |
| **Life Log** | Vulcan autobiography | Markdown (Journal entries) + SQLite Timeline | "Installed Git skill", "Completed Phase 2", "Model configurations updated" |
| **Reflection Memory**| System Self-Correction | Markdown + SQLite Summary | "What worked?", "What mistakes am I making?", "How have preferences changed?" |
| **Identity Memory** | Core System Identity | Markdown + Local Config | Constitution, Installed skills, Core values, Current version |

---

## 4. The Memory Council & Extractive Pipeline

Memory does not appear out of nowhere. Instead, it transitions through a structured pipeline coordinated by the **Memory Council**:

```
Conversation End / Trigger
           |
           v
   +---------------+
   | Memory Council| <--- Determines if extraction is needed (Heuristics/LLM)
   +-------+-------+
           | (Yes)
           v
   +---------------+
   |   Extractor   | <--- Generates CandidateMemory objects from conversation
   +-------+-------+
           |
           v
   +---------------+
   |   Classifier  | <--- Determines Category (Fact, Preference, Goal, etc.)
   +-------+-------+
           |
           v
   +---------------+
   |   Validator   | <--- Assigns Confidence & Importance scores
   +-------+-------+
           |
           v
   +---------------+
   |  Consolidator | <--- Detects duplicates, merges with existing files/headings
   +-------+-------+
           |
           v
   +---------------+
   |   Governance  | <--- Enforces privacy, conflict resolution, and retention policies
   +-------+-------+
           |
           v
    Storage Layer (Obsidian Vault, SQLite Catalog, ChromaDB Vectors)
```

### 4.1 Memory Governance

Located under `vulcan/memory/governance.py`, this layer serves as Vulcan's "memory conscience." It governs:
*   **Duplicate Detection**: Ensures duplicate facts are not written repeatedly.
*   **Conflict Resolution**: If a new fact contradicts an older one (e.g., Favorite IDE switches from VSCode to Cursor), it handles archiving the old version.
*   **Privacy Policies**: Prevents storage of highly sensitive or explicitly restricted information.
*   **Retention Policies**: Manages fading or archiving low-importance memories over time.

---

## 5. Metadata Schema & Versioning

All memories carry rich metadata embedded inside Obsidian Markdown as YAML Frontmatter:

```yaml
---
uuid: "a3b9f4e2-8d7c-4a3b-9e2c-1d3f4e5a6b7c"
memory_type: "knowledge"
category: "preference"
importance: "high"
confidence: 0.95
created: "2026-08-03T14:30:00Z"
updated: "2026-08-03T14:30:00Z"
version: 1
source: "conversation"
correlation_id: "7d6c5b4a-3f2e-1d0c-9b8a-7e6d5c4b3a21"
relationships:
  - { target_uuid: "b2c3d4e5-...", relation: "Uses" }
tags:
  - "ide"
  - "developer-tools"
---
```

### 5.1 Versioning Model

To preserve historical accuracy, Vulcan never overwrites memory files. Instead, it implements a history archive:
*   The primary active memory is kept clean and readable at its standard path (e.g., `Users/Shreyas/Preferences.md`).
*   When an update occurs, the old version is written to a hidden history directory: `.history/Users/Shreyas/Preferences_v1.md`.
*   The new version is updated at the active path with its version number incremented in the frontmatter.

---

## 6. Retrieval Engine

Memory retrieval combines multiple dimensions to construct a unified context score:

$$\text{Unified Score} = w_{\text{sim}} \cdot \text{Similarity} + w_{\text{rec}} \cdot \text{Recency} + w_{\text{imp}} \cdot \text{Importance} + w_{\text{conf}} \cdot \text{Confidence}$$

Retrieval is parameterized through a `RetrievalPolicy` (stored in the system configuration), allowing Vulcan to adapt its recall strategy depending on the task (e.g., precise coding task vs. creative brainstorming vs. reflection).

---

## 7. Future Evolution

The design of Vulcan's memory subsystem is future-proofed for the following expansions:
1.  **Collaborative Agent Memory**: By segmenting Obsidian subfolders by agent namespace (e.g., `Agents/DevAgent/`), multiple specialized agents can safely read/write their own identity and work context.
2.  **Decade-scale Vector Pruning**: Low-importance vectors in ChromaDB can be pruned safely based on SQLite retrieval frequency statistics without losing the human-readable Markdown source in Obsidian.
3.  **Human-in-the-Loop Approval**: The Memory Council can easily route CandidateMemories to a UI panel for manual human editing, approval, or deletion before committing them to the permanent storage providers.
