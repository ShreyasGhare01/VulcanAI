"""Cognitive Core Subsystem package.

Responsibility:
    Responsible for coordinating all dialogue states, assembling contextual awareness pieces,
    constructing system prompts, making hybrid planner decisions, executing the central cognitive loop,
    and managing conversational session histories.

Dependencies:
    - vulcan/config/ (VulcanConfig)
    - vulcan/core/ (CommandBus, EventBus, CapabilityRegistry)
    - vulcan/services/ (IInferenceProvider)

Public Interfaces:
    - CognitiveRouter
    - SessionManager
    - PromptBuilder
    - Planner
    - ContextAssemblyPipeline
    - ContextBudgetManager

Forbidden Dependencies:
    - No presentation layers or UI widgets (vulcan/ui/) may be imported here.
"""
