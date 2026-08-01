# Vulcan AI Operating System - Architecture Specification

Welcome to Vulcan, an extensible, highly modular, event-driven AI Operating System. This document details the architectural specification, extension points, and coding guidelines.

---

## 1. Threading Philosophy

To ensure smooth visual execution at 60 FPS across multi-monitor displays, Vulcan implements a strict threading separation:
- **Presentation Threading**: The main thread coordinates exclusively with PySide6 visual rendering, layouts, and window coordinate restoration. No blocking network or heavy database operations are permitted on the main thread.
- **Infrastructure Threading**: Background execution (such as LLM generation, vector search, speech recognition, and file compiling) belongs entirely to the infrastructure/orchestration layer. Background execution must never leak into visual models directly; status updates and outputs are marshalled to the main thread via timezone-aware hierarchical notifications on the `EventBus`.

---

## 2. Command Bus vs Event Bus

Vulcan separates requests (what should happen) from facts (what already happened):
- **Command Bus**:
  - Directs explicit requests to handlers (e.g. `Skill.Filesystem.Read`).
  - Expects synchronous or futures-based execution return values.
  - Implemented inside `vulcan/core/command_bus.py`.
- **Event Bus**:
  - Broadcasts notification facts to zero or more decoupled observers (e.g. `System.Started`, `Memory.Stored`).
  - Supports cascading/hierarchical namespaces (e.g. `System.*` receives `System.Started`).
  - Implemented inside `vulcan/core/event_bus.py`.

---

## 3. Extension & Plugin Development Guide

### How to Add a New Skill
1. Create a subpackage folder inside `vulcan/skills/` (e.g., `git`).
2. Define a `manifest.json` containing `"manifest_version": 1`, permissions, and exposed capabilities.
3. Write your concrete class implementing `ISkill` (defined in `vulcan/agents/framework.py`).
4. Upon application startup, `SkillLoader` scans the folder, validates the schema version, and registers the skill pack dynamically.
