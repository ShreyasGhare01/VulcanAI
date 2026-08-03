# VulcanAI Master Development Roadmap

This document establishes the official engineering roadmap and master development plan for the Vulcan AI Operating System. Rather than serving as an issue tracker or simple feature list, this roadmap details the technical vision, architectural dependencies, success metrics, and design constraints across all ten development phases (0–9).

The goal of this document is to ensure that all core developers and open-source contributors understand not only *what* is being built, but also *why* features are implemented in a specific sequence, and why certain concepts are intentionally deferred.

---

## Roadmap Overview

```
                      ┌────────────────────────────────────────┐
                      │    Phase 0: Architectural Foundation   │  ✅ Completed
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │        Phase 1: Cognitive Core         │  ✅ Completed
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │       Phase 2: Memory & Context        │  🚧 In Progress
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │   Phase 3: Skills & Capability Fmwk    │  ⬜ Planned
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │         Phase 4: Voice Interface       │  ⬜ Planned
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │      Phase 5: Planning & Workflows     │  ⬜ Planned
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │      Phase 6: Multi-Agent System       │  ⬜ Planned
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │       Phase 7: Development Agent       │  ⬜ Planned
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │     Phase 8: Autonomous Improvement    │  ⬜ Planned
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │      Phase 9: AI Operating System      │  ⬜ Planned
                      └────────────────────────────────────────┘
```

---

## Phase 0 — Architectural Foundation

### Status
✅ Completed

### Objective
Establish the primary system architecture patterns, core package layout boundaries, basic UI structures, and asynchronous/synchronous messaging infrastructure. Guarantee strict separation of concerns before building any high-level AI or planning capabilities.

### Major Deliverables / Milestones
*   **Package Namespace Layout:** Enforce unified `vulcan` root package layout.
*   **Decoupled Communication Backbone:** Implement the asynchronous pattern-matching `EventBus` and synchronous `CommandBus`.
*   **Dependency Injection Container:** Build the central `ServiceContainer` mapping interfaces to implementations.
*   **Capability Registry:** Create a thread-safe registry to catalog functional abilities and permissions.
*   **Unified Configuration Engine:** Design layered configuration supporting defaults, files, environment variables, and runtime overrides.
*   **Dockable GUI Shell:** Implement PySide6 interface using `QDockWidget` with state saving and restoration (`saveState`/`restoreState`).
*   **Governance Documentation:** Formalize `Constitution.md`, `Vulcan_Architecture_Specification.md`, and initial ADRs.

### Success Criteria
*   Zero circular or vertical layer dependency violations (validated by Ruff/MyPy).
*   UI layout and dock configurations persist reliably across application restarts.
*   All unit and PySide6 integration tests execute successfully under Pytest and Pytest-Qt.

### Dependencies
*   Python 3.10+, PySide6, and the standard library testing framework.

### Explicitly Out of Scope
*   Live local language model (LLM) interaction or chat histories.
*   Semantic memory storage or vector indexing.
*   Actual filesystem or system execution operations.

---

## Phase 1 — Cognitive Core

### Status
✅ Completed

### Objective
Develop Vulcan's primary reasoning loop. Create a model-provider abstraction layer, formalize session management, compile environmental context, and build deterministic and LLM planning routing to process simple conversational turns.

### Major Deliverables / Milestones
*   **Model-Provider Abstraction:** Implement `IInferenceProvider` interface and construct `OllamaProvider` using robust `httpx` adapters.
*   **Deterministic Reasoning Layer:** Integrate a heuristic rule planner to instantly catch empty, system, or diagnostic inputs without invoking LLMs.
*   **Pluggable Context Pipeline:** Implement `IContextProvider` to collect environmental variables, configurations, active capabilities, and session properties into structured `ContextPiece` objects.
*   **Prompt Builder:** Build an assembly pipeline to compile structured, replaceable, and testable prompt sections.
*   **Unified Cognitive Loop Router:** Establish `CognitiveRouter` to sequentialize message input, context compilation, prompt builder execution, inference, and response dispatching.
*   **Interactive Chat UI:** Provide functional chat widgets, token tracking panels, and background execution threading for non-blocking UI rendering.

### Success Criteria
*   The system detects and executes diagnostic commands (e.g., shutdown, UI layout resets) deterministically.
*   Conversation processing runs on a dedicated background thread without causing GUI stutters.
*   Inference degrades gracefully with custom `MODEL_UNAVAILABLE` fallbacks when the local Ollama service is offline.

### Dependencies
*   Phase 0 Architectural Foundation.
*   Local Ollama installation and access to Qwen/similar GGUF models.

### Explicitly Out of Scope
*   Long-term persistent memory across sessions.
*   Executing state-altering bash scripts or file edits.
*   Subordinate agent creation or task delegation.

---

## Phase 2 — Memory & Context

### Status
🚧 In Progress

### Objective
Implement the multi-domain memory framework, enabling long-term persistence across user sessions. Bridge semantic vector search (ChromaDB) with relational timeline logs (SQLite) and establish a respectful, non-destructive bridge to the user's personal Obsidian knowledge vault.

### Major Deliverables / Milestones
*   **Relational Storage Layer:** Create relational databases for conversations, turn histories, system status records, and experience logs.
*   **ChromaDB Vector Integration:** Provide a fully-typed vector search adapter implementing semantic knowledge storage.
*   **Obsidian User Memory Interface:** Establish the `IUserMemory` provider to read and carefully interface with the user's personal vault files.
*   **Context Budget Manager:** Build dynamic truncation, sliding window prompts, and vector similarity thresholds to prevent LLM context overflows.
*   **Life Log Subsystem:** Implement a chronological structured event log recording autonomous milestones separate from system debug files.
*   **Memory Consolidation Service:** Build background routines to synthesize dialogue turns, summarize active experiences, and store key observations in reflection memory.

### Success Criteria
*   The system retrieves relevant historical context from past sessions when a matching prompt topic is raised.
*   Obsidian files are accessed read-only by default, and modified only through explicit, verified transactions.
*   The application tracks and displays memory vector metrics and db sizes inside the GUI diagnostic docks.

### Dependencies
*   Phase 1 Cognitive Core.
*   SQLite standard library hooks and local ChromaDB bindings.

### Explicitly Out of Scope
*   Invoking external terminal shells or editing code files.
*   Exposing agent tools or capability APIs to the prompt builder.

---

## Phase 3 — Skills & Capability Framework

### Status
⬜ Planned

### Objective
Transition Vulcan from a conversational system into an actionable desktop tool. Allow the Cognitive Router and Planner to select, permission-gate, and invoke local system capabilities through the unified Command Bus.

### Major Deliverables / Milestones
*   **First-Party Skill Packages:** Develop standard modules for safe filesystem read/writes, git branch audits, browser searching, and local terminal execution.
*   **Manifest Validation Engine:** Validate dynamic `manifest.json` schemas containing `manifest_version` declarations and permission maps.
*   **The Tool Execution Engine:** Map Pydantic-defined tool schemas into prompt capability definitions.
*   **Permission Gatekeepers:** Force manual visual approval prompts inside the PySide6 UI whenever a capability requests access outside the workspace boundaries.
*   **Dynamic Command Handlers:** Bind capability tool triggers to specific Command Bus execution streams.

### Success Criteria
*   The Planner successfully generates tool calls that match capability parameters.
*   All file edits outside the primary workspace path are blocked automatically unless overriding permissions are confirmed by the user.
*   Developers can register a new skill simply by adding a directory containing a valid manifest.

### Dependencies
*   Phase 2 Memory & Context.

### Explicitly Out of Scope
*   Multi-agent coordination or delegation.
*   Complex multi-step task generation and workflows (execution is strictly limited to single immediate capabilities).

---

## Phase 4 — Voice Interface

### Status
⬜ Planned

### Objective
Incorporate physical desktop presence by adding voice inputs and outputs. Empower users to converse with their local assistant hands-free.

### Major Deliverables / Milestones
*   **Local Wake Word Engine:** Integrate light-weight local wake word detection (e.g., openwakeword or similar).
*   **Streaming Speech-to-Text (STT):** Deploy Whisper or similar local models to translate spoken words into text streams.
*   **Voice Activity Detection (VAD):** Build silences-and-interruption handlers to halt TTS output if the user starts speaking.
*   **Local Text-to-Speech (TTS):** Integrate local streaming TTS (e.g., Piper, Kokoro) to synthesize responsive natural speech.
*   **PySide6 Audio Controls:** Design an audio dashboard dock displaying input volumes, active listening states, and mute controls.

### Success Criteria
*   Audio processing runs entirely on dedicated background threads, maintaining visual UI fluidity.
*   TTS streaming starts within 500ms of the local model concluding its reasoning turn.
*   Interruption detection successfully pauses speaking queues as soon as user voice inputs are registered.

### Dependencies
*   Phase 3 Skills & Capability Framework.

### Explicitly Out of Scope
*   Complex audio recording storage.
*   Voice-based authentication or cryptographic key unlocking.

---

## Phase 5 — Planning & Workflows

### Status
⬜ Planned

### Objective
Empower Vulcan to accomplish complex, multi-stage goals. Move past immediate query-response structures toward sustained, persistent task planning, tracking, and recovery.

### Major Deliverables / Milestones
*   **Hierarchical Plan Generation:** Upgrade Planners to decompose high-level objectives into tree-like structures of dependent, executable `Task` nodes.
*   **State-Aware Workflow Coordinator:** Build scheduling queues that can suspend, resume, or abort long-running multi-step processes.
*   **Workflow Persistence:** Save active plan trees, variable state mappings, and execution logs in SQLite so state can survive application restarts.
*   **Visual Planner Monitor:** Build a interactive workflow diagram dock in PySide6 to display task nodes, current statuses (Pending, Running, Complete, Failed), and active variables.

### Success Criteria
*   Vulcan completes a multi-step objective (e.g., "Find all Markdown files, extract headers, and generate a summary report") without manual user intervention for intermediate steps.
*   If a sub-task fails, the planner performs a structured exception handling loop (e.g., retrying or proposing a workaround).

### Dependencies
*   Phase 3 Skills & Capability Framework.

### Explicitly Out of Scope
*   Spawning separate subordinate agent runtimes.
*   Direct code creation or automated self-modifications.

---

## Phase 6 — Multi-Agent System

### Status
⬜ Planned

### Objective
Introduce agent specialization and task delegation. Transition Vulcan from a single reasoning core into a cooperative swarm of localized virtual specialists.

### Major Deliverables / Milestones
*   **Agent Definition Engine:** Model specialized system personas (e.g., Researcher, Coder, Tech Writer, Tester) with custom prompts and gated capabilities.
*   **Context-Based Message Routing:** Build channels for agents to exchange queries, share context pieces, and propose solutions.
*   **Sovereign Human-in-the-Loop Gate:** Create a central dashboard where the user reviews, approves, or edits communication and action proposals exchanged between subordinate agents.
*   **Cooperative Workspace Management:** Allow agents to checkout sandbox directories and share localized temporary database workspaces.

### Success Criteria
*   The primary coordinator agent successfully assigns a code compilation task to the Coder Agent and a document evaluation task to the Technical Writer.
*   Sub-agents communicate and share outputs securely using JSON formats over the Event Bus.

### Dependencies
*   Phase 5 Planning & Workflows.

### Explicitly Out of Scope
*   Autonomous changes to the primary repository codebase.
*   Direct network-to-network inter-device agent orchestration.

---

## Phase 7 — Development Agent

### Status
⬜ Planned

### Objective
Equip Vulcan with the capabilities to safely maintain and evolve its own codebase under strict human supervision. Enable the AI to develop, test, and package new first-party skills.

### Major Deliverables / Milestones
*   **Strict Execution Sandbox:** Establish a completely isolated docker or folder-level workspace sandbox.
*   **Automated Git Operations:** Enable the agent to create dedicated feature branches, stage changes, and compile descriptive commits.
*   **Local Test & Lint Runners:** Integrate background runners executing `pytest`, `black`, `ruff`, and `mypy` against modified code.
*   **Code Review Pipeline:** Program a self-critic review loop comparing the generated codebase with the rules in the VAS and Constitution.
*   **Supervised PR Generator:** Output formatted, structured pull requests and await human authorization before executing local branch merges.

### Success Criteria
*   Vulcan successfully develops a new, fully functional basic capability (e.g., a simple Calculator Skill), passes all linting and test rules inside the sandbox, and generates a valid PR.
*   Any syntax or static typing error triggers automated self-repair loops within the sandbox.

### Dependencies
*   Phase 6 Multi-Agent System.

### Explicitly Out of Scope
*   Modifying the active runtime codebase or the master/main branches directly.
*   Pushing code to remote repositories without manual human security review.

---

## Phase 8 — Autonomous Improvement

### Status
⬜ Planned

### Objective
Allow Vulcan to learn from experience. Establish continuous optimization loops where the system reviews historical Life Logs, identifies latency or performance bottlenecks, refines prompts, and optimizes memory structures.

### Major Deliverables / Milestones
*   **Life Log Reflection Engine:** Develop background analytical agents that parse the system's Life Log to find failed plans or repetitive behaviors.
*   **Self-Driven Prompt Optimizer:** Automatically adjust system prompts and agent instruction sets to improve output clarity and reduce token consumption.
*   **Memory Pruning & Compression:** Synthesize sparse vector points into high-density reflection summaries, removing redundant or irrelevant historical records.
*   **Structural Optimization Proposals:** Generate readable system enhancement reports proposing new capability pathways or alternative configurations.

### Success Criteria
*   The system successfully identifies redundant prompts or circular workflow behaviors in past logs and modifies its internal persona rules to prevent them.
*   Semantic vector search latency remains flat or decreases over prolonged use due to automated index pruning.

### Dependencies
*   Phase 7 Development Agent.

### Explicitly Out of Scope
*   Altering architectural boundaries, interfaces, or Constitutional articles.

---

## Phase 9 — AI Operating System

### Status
⬜ Planned

### Objective
Unify every subsystem into a persistent, modular, and highly polished AI Operating System. Realize Vulcan as a cohesive computing companion capable of managing your local hardware, digital knowledge, and professional workflows natively.

### Major Deliverables / Milestones
*   **Persistent Desktop Daemon:** Run Vulcan as a background OS process with minimal idle memory consumption.
*   **Unified Voice, Vision & UI Channels:** Allow users to seamlessly transition between voice commands, screen-capture inputs, desktop chats, and dockable widgets.
*   **Global Knowledge & Event Integration:** Bind Vulcan directly to local file modifications, incoming emails, or calendar notifications via safe OS-level event listeners.
*   **Full Swarm Automation:** Orchestrate background swarms of specialized agents executing complex research, software development, and life-logging tasks simultaneously.
*   **Self-Healing Architecture:** Let the system automatically patch minor runtime exceptions, compile optimized libraries, and upgrade skill dependencies.

### Success Criteria
*   Vulcan serves as a fully featured, persistent desktop companion capable of handling end-to-end multi-hour development, automation, and research activities locally.
*   System resource utilization scales cleanly, respecting the user's running applications and workstation constraints.

### Dependencies
*   All prior phases (0 through 8).

### Explicitly Out of Scope
*   Closed-source commercialization of core system features.
*   Replacing native host OS security or hardware abstraction policies.
