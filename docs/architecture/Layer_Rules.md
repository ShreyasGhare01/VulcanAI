# Vulcan Layer Rules

This document outlines the architectural boundaries and dependency direction rules enforced across the Vulcan AI OS.

---

## 1. Architectural Layers & Responsibilities

The system is organized into four classic decoupled vertical layers:

```
  +-------------------------------------------------+
  |              Presentation Layer                 | (UI, CLI, Voice, Speech-to-Text)
  +-----------------------+-------------------------+
                          |
                          v
  +-------------------------------------------------+
  |              Orchestration Layer                | (Planner, Workflow, Agent Tasks, Commands)
  +-----------------------+-------------------------+
                          |
                          v
  +-------------------------------------------------+
  |                 Domain Layer                    | (Memory interfaces, Registry, SkillManifest)
  +-----------------------+-------------------------+
                          |
                          v
  +-------------------------------------------------+
  |             Infrastructure Layer                | (Ollama, SQLite, ChromaDB, Git, Filesystem)
  +-------------------------------------------------+
```

### A. Presentation Layer
- **Components**: UI views (PySide6), CLI tools, sound/voice notifications.
- **Rules**:
  - Must be as thin as possible.
  - No business rules or AI orchestration logic can live inside this layer.
  - May interact with the Orchestration Layer via controllers, dispatching commands, and listening to events on the `EventBus`.

### B. Orchestration Layer
- **Components**: Planner, agent coordination, workflow execution, task scheduler, command routing.
- **Rules**:
  - Translates user requests from the Presentation Layer into concrete task sequences.
  - Directs domain capabilities via the `CommandBus`.

### C. Domain Layer
- **Components**: Capability registration, memory abstractions, skill manifests, agent definitions, core business rules.
- **Rules**:
  - Contains strictly pure Python types, Pydantic models, and abstract contracts.
  - **Completely independent of UI, Qt, or external network frameworks.**

### D. Infrastructure Layer
- **Components**: Ollama provider client, sqlite database persistence, ChromaDB vector collection, workspace files, Git interaction.
- **Rules**:
  - Implements the abstract contracts declared in the Domain Layer.
  - Restricts network/database dependencies strictly behind stable interfaces.

---

## 2. Dependency Flow Law (Inward Flow)

1. Dependencies must **always flow inward** (downward in the diagram).
2. **Forbidden**: Infrastructure or Domain modules are strictly forbidden from importing from the Presentation Layer. (e.g. `import PySide6` or `from vulcan.ui.main_window import ...` inside `vulcan/core/` is an architectural violation).
3. **Forbidden**: Circular imports.

---

## 3. Communication Standards

- **Commands** (Requests to execute an action) are routed from Presentation/Orchestration downward via the `CommandBus`.
- **Events** (Facts that already happened) are published upward or across layers via the `EventBus`.
