# Vulcan Architectural Glossary

This glossary contains the canonical, single-source definitions for all key architectural terms, entities, and concepts used throughout the Vulcan AI Operating System. All other documentation, architecture specifications, decision records, and codebase variables must align strictly with these definitions.

---

## A
### Agent
A discrete, autonomous software entity equipped with a specific **role**, a set of objectives, and access to **capabilities**. Agents operate under the guidance of the **Orchestrator** and utilize **Planners** to solve complex tasks.

### Agent Framework
The abstract base classes, lifecycles, and coordination patterns (defined in `vulcan/agents/framework.py`) that govern how agents are initialized, assigned tasks, and executed.

### Architecture Decision Record (ADR)
A document that captures a significant architectural decision made for the project, including its context, alternatives considered, decision, consequences, and tradeoffs.

---

## C
### Capability
A concrete, permission-gated functional action (such as `filesystem.read` or `filesystem.write`) registered in the **Capability Registry**. Capabilities are exposed by **Skills** or core modules and routed dynamically.

### Capability Registry
The central, thread-safe directory (`CapabilityRegistry` in `vulcan/core/registry.py`) where all available capabilities, their input/output schemas, providers, and permissions are registered and looked up at runtime.

### Command
A request or instruction to perform a specific action, representing intent (*what should happen*). Commands are routed from higher layers (Presentation/Orchestration) downward through the **Command Bus**.

### Command Bus
The synchronous or futures-based message routing mechanism (`CommandBus` in `vulcan/core/command_bus.py`) responsible for dispatching **Commands** to exactly one registered handler.

### Context
A structured dictionary of key-value pairs or metadata representing the environmental state, session parameters, and background information relevant to an active execution, LLM query, or task.

---

## E
### Event
A historical, immutable notification representing a completed fact (*what already happened*). Events are published upward or across layers to communicate state changes.

### Event Bus
The asynchronous, decoupled messaging backbone (`EventBus` in `vulcan/core/event_bus.py`) that distributes hierarchical namespace-aware **Events** (e.g., `System.Started`) to zero or more registered observers.

---

## L
### Life Log
A structured, persistent chronological timeline documenting the system's autonomous reasoning, decisions, milestones, LLM interactions, and executed capabilities. It is distinct from ordinary application debugging logs.

---

## M
### Memory
The complete persistent and volatile storage system enabling Vulcan to retain state, track experiences, and recall knowledge over time. It is divided into distinct, non-overlapping domains coordinated by the **Memory Manager**.

### Memory Manager
The storage-agnostic orchestrating service (`IMemoryManager`) that provides access to the distinct memory sub-systems.

### Memory Domain
One of the seven distinct partitions of the memory architecture:
*   **Working Memory**: Tracking of the active task, sub-tasks, and current workflow context.
*   **Identity Memory**: Immutable and mutable system configurations, identity keys, and personality profiles.
*   **Experience Memory**: Historical, chronological timeline of actions, notifications, and events.
*   **Knowledge Memory**: Semantic fact storage and background information retrieved via vector search.
*   **Reflection Memory**: Synthesized summaries, evaluations, and compiled performance reports.
*   **Development Memory**: Workspace code structure, module tracking, and codebase-specific documentation.
*   **User Memory**: The user's external, personal knowledge vault (typically Obsidian-backed).

### Model Provider
An abstraction layer (`IInferenceProvider`) masking the specific LLM execution backend, ensuring Vulcan remains backend-agnostic.

---

## O
### Orchestrator
The central planning and control subsystem responsible for breaking down a high-level user objective into structured tasks, assigning them to agents, and driving execution to completion.

---

## P
### Planner
The system component (`IPlanner`) responsible for constructing a logical sequence of **Tasks** based on a user-defined objective and the current system **Context**.

### Plugin
An extensible third-party package loaded dynamically from `vulcan/plugins/` to inject new infrastructure providers, tools, or integrations into Vulcan.

### Provider
A concrete implementation of a service contract or capability interface (e.g., `OllamaProvider` is a model provider; `ChromaService` is a vector store provider).

---

## S
### Service
A long-lived, lifecycle-managed core system component (e.g., Database, Inference Provider, Event Bus) registered inside the **Service Container**.

### Service Container
The dependency injection container (`ServiceContainer` in `vulcan/core/container.py`) that manages the lifecycles, configuration, and resolution of core services.

### Skill
A high-level, independent package of functionality containing a manifest, configuration, documentation, tests, and code exposing one or more **Capabilities** and **Tools** (e.g., the filesystem skill).

---

## T
### Task
A discrete, structured unit of execution assigned to an **Agent**.

### Tool
A fine-grained, executable function with a defined input/output schema that an LLM or agent can invoke to perform operations.

---

## W
### Workspace
The sandboxed directory on the local filesystem (defined in `AppConfig.workspace_dir`) containing the files, databases, and logs that Vulcan has permission to interact with.
