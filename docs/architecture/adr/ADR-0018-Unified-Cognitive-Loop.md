# ADR-0018: Unified Cognitive Loop

## Status
Accepted

## Context
A major risk in AI Operating Systems is the sprawl of ad hoc LLM prompts, direct skill calls, and tight integration between visual widgets and raw inference APIs. This makes components highly brittle, difficult to test, and prone to catastrophic failure.

## Decision
We establish a single Authoritative **Cognitive Loop** processing pipeline that governs all user-machine interactions in Vulcan:
```
User Input
        ↓
Session Manager
        ↓
Context Assembly
        ↓
Prompt Builder
        ↓
Inference Provider
        ↓
Planner
        ↓
Router
        ↓
Command Bus
        ↓
Capability
        ↓
Event Bus
        ↓
Session Update
        ↓
UI Response
```
All autonomous actions, capability dispatches, and dialogue generations must follow this sequential, auditable loop flow.

## Why was this chosen instead of the obvious alternative?
- **Alternative considered**: Direct routing where agents or skills can execute capabilities independently or bypass the central loop.
- **Why rejected**: Allowing individual subsystems to query LLMs directly or dispatch commands without a centralized state machine results in a chaotic, non-auditable workspace. Bypassing the central Cognitive Loop makes it impossible to implement a consistent Life Log, limits safety/permissions verification, and prevents the UI thread from displaying real-time cognitive transitions. A unified loop ensures absolute transparency, safety, and a single track of reasoning.

## Consequences
- Deep observability into every stage of reasoning.
- Clear tracking with matching UUIDs: Session ID, Inference ID, Decision ID, and Event IDs.
- Bulletproof separation of UI and domain execution paths.

## Future Evolution
Future capabilities—such as voice integration, agent reflection steps, multi-agent workspaces, and memory storage—can easily plug into the loop via standard command handlers or event subscribers rather than bypassing or modifying the cognitive engine.
