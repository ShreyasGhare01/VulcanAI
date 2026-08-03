# ADR-0017: Cognitive Core Architecture

## Status
Accepted

## Context
As Vulcan shifts from a static framework to an active AI Operating System, we require an organized subsystem that models the flow of user communication, gathers environmental status, builds sequential model prompts, runs inference requests safely behind a generic provider abstraction, parses responses, and executes planning decisions.

To achieve this, we introduce the **Cognitive Core** (`vulcan/cognition/`).

## Decision
We implement a decoupled orchestration architecture inside `vulcan/cognition/` containing:
1.  **Conversation Sessions**: Strongly typed message tracks (`UserMessage`, `AssistantMessage`, `SystemMessage`) organized under `ConversationSession` in `vulcan/cognition/session.py`.
2.  **Context Pipeline**: Pluggable providers contributing structured `ContextPiece` objects assembled dynamically by `ContextAssemblyPipeline`.
3.  **Prompt Builder**: An assembler sequentially stacking sections (Identity, Operating Rules, Session, Context, Capabilities, Task, User Input).
4.  **Inference Orchestration**: Pure model-agnostic completions routed via `IInferenceProvider` (not vendor lock-in APIs).
5.  **Planning Engine**: A hybrid rule-based and LLM-fallback classification decider returning typed `PlannerDecision` objects.
6.  **Cognitive Loop Router**: A central traffic controller separating plans from concrete skill or command-bus execution pathways.

## Why was this chosen instead of the obvious alternative?
- **Alternative considered**: Direct, monolithic string assembly inside UI widgets or script-like controllers.
- **Why rejected**: A script-based or direct chatbot pattern tightly couples inference APIs to visual rendering. It prevents offline fallbacks, leads to fragile prompt concatenation scattered across the app, and makes automated testing impossible. Choosing a decoupled Cognitive Core with standard interfaces ensures that we can unit test every stage of cognition (session, context, prompt, metrics) independently of PySide6 or the live network state.

## Consequences
- Business logic is strictly separated from presentation UI layers.
- Prompts are organized, testable, and deterministic, eliminating unstructured string concatenation.
- The system achieves high resiliency, adapting gracefully when local providers are offline.

## Future Evolution
The `IInferenceProvider` interface can easily swap llama.cpp, vLLM, or secure remote models without breaking prompt construction. Additional context providers (such as vector memory, Obsidian vaults, or task pipelines) can register directly into the assembly pipeline without modifying cognitive code.
