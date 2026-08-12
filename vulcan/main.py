"""Vulcan Entrypoint and Boot Composition Script."""

import sys

from PySide6.QtWidgets import QApplication

from vulcan.cognition.context import (
    ActiveTaskProvider,
    ApplicationStatusProvider,
    AvailableCapabilitiesProvider,
    ContextAssemblyPipeline,
    CurrentConfigurationProvider,
    IdentityContextProvider,
    SessionContextProvider,
    MemoryContextProvider,
)
from vulcan.cognition.identity import IdentityProvider
from vulcan.cognition.planner import Planner
from vulcan.cognition.prompt_builder import PromptBuilder
from vulcan.cognition.router import CognitiveRouter
from vulcan.cognition.session import SessionManager
from vulcan.config import VulcanConfig
from vulcan.core.bootstrap import Bootstrapper
from vulcan.core.command_bus import ICommandBus
from vulcan.core.command_handlers import SystemCommandHandler
from vulcan.core.event_bus import IEventBus
from vulcan.core.registry import ICapabilityRegistry
from vulcan.core.skills_loader import SkillLoader
from vulcan.services.chroma import ChromaService, IChromaService
from vulcan.services.inference import IInferenceProvider, OllamaProvider
from vulcan.ui.controller import UIController
from vulcan.ui.main_window import VulcanMainWindow


def main() -> int:
    # 1. Boot core subsystems
    bootstrapper = Bootstrapper()
    container = bootstrapper.boot()

    # 2. Extract configuration, buses, and registries
    config = container.resolve(VulcanConfig)
    event_bus = container.resolve(IEventBus)
    command_bus = container.resolve(ICommandBus)
    registry = container.resolve(ICapabilityRegistry)

    # 3. Instantiate and register infrastructure services
    inference_provider = OllamaProvider(config.model)
    inference_provider.initialize()
    container.register(IInferenceProvider, inference_provider)

    chroma_service = ChromaService(config.chroma)
    chroma_service.initialize()
    container.register(IChromaService, chroma_service)

    # 4. Perform dynamic skills loader scan with explicit injection
    skills_loader = SkillLoader(registry=registry)
    skills_loader.discover_and_register_all()

    # 5. Initialize Persistent Memory Manager & Context
    from vulcan.memory.interfaces import IMemoryManager
    from vulcan.memory.manager import MemoryManager

    memory_manager = MemoryManager(
        config=config,
        inference_provider=inference_provider,
        event_bus=event_bus,
        chroma_service=chroma_service,
    )
    container.register(IMemoryManager, memory_manager)

    # Automatically drain pending offline memory queue at startup when Ollama is online
    if inference_provider.is_online():
        try:
            memory_manager.council.process_pending_queue()
        except Exception:
            pass

    # 6. Initialize the Cognitive Core
    session_manager = SessionManager()
    session_manager.create_session()  # Initialize first default session

    identity_provider = IdentityProvider(config)

    # Context gathering pipeline assembly
    context_pipeline = ContextAssemblyPipeline()
    context_pipeline.register_provider(SessionContextProvider(session_manager))
    context_pipeline.register_provider(ApplicationStatusProvider())
    context_pipeline.register_provider(CurrentConfigurationProvider(config))
    context_pipeline.register_provider(AvailableCapabilitiesProvider(registry))
    context_pipeline.register_provider(ActiveTaskProvider(session_manager))
    context_pipeline.register_provider(IdentityContextProvider(identity_provider))
    context_pipeline.register_provider(MemoryContextProvider(memory_manager))

    prompt_builder = PromptBuilder()
    planner = Planner(inference_provider)

    cognitive_router = CognitiveRouter(
        session_manager=session_manager,
        context_pipeline=context_pipeline,
        prompt_builder=prompt_builder,
        inference_provider=inference_provider,
        planner=planner,
        command_bus=command_bus,
        event_bus=event_bus,
        memory_manager=memory_manager,
    )

    # Setup core system command handlers
    command_handler = SystemCommandHandler(command_bus, event_bus)
    command_handler.initialize_standard_handlers()

    # 6. Build presentation layer with explicit Constructor Injection (No locator calls inside UI)
    app = QApplication(sys.argv)
    controller = UIController(
        config=config,
        registry=registry,
        inference=inference_provider,
        cognitive_router=cognitive_router,
    )
    window = VulcanMainWindow(controller)
    window.show()

    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
