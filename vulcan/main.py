"""Vulcan Entrypoint and Boot Composition Script."""

import sys

from PySide6.QtWidgets import QApplication

from vulcan.config import VulcanConfig
from vulcan.core.bootstrap import Bootstrapper
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

    # 2. Extract configuration
    config = container.resolve(VulcanConfig)

    # 3. Instantiate and register infrastructure services
    inference_provider = OllamaProvider(config.model)
    inference_provider.initialize()
    container.register(IInferenceProvider, inference_provider)

    chroma_service = ChromaService(config.chroma)
    chroma_service.initialize()
    container.register(IChromaService, chroma_service)

    # 4. Perform dynamic skills loader scan with explicit injection
    registry = container.resolve(ICapabilityRegistry)
    skills_loader = SkillLoader(registry=registry)
    skills_loader.discover_and_register_all()

    # 5. Build presentation layer with explicit Constructor Injection (No locator calls inside UI)
    app = QApplication(sys.argv)
    controller = UIController(
        config=config,
        registry=registry,
        inference=inference_provider,
    )
    window = VulcanMainWindow(controller)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
