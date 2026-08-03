"""Core Subsystem package.

Responsibility:
    Responsible for core Operating System services, including the Service DI Container,
    the Event Bus, the Command Bus, the Capability Registry, skills dynamic loader mechanisms,
    and strongly-typed execution context scopes.

Dependencies:
    - Pure python structures and domain types.

Public Interfaces:
    - ServiceContainer
    - EventBus, IEventBus
    - CommandBus, ICommandBus
    - CapabilityRegistry, ICapabilityRegistry
    - SkillLoader
    - Bootstrapper

Forbidden Dependencies:
    - No presentation layers or UI widgets (vulcan/ui/) may be imported here.
    - No direct language model providers or external endpoints.
"""
