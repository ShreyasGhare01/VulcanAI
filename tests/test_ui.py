from typing import Any

from vulcan.ui.controller import MockUIController
from vulcan.ui.main_window import VulcanMainWindow


def test_ui_controller_mock_behaviors() -> None:
    controller = MockUIController()
    status = controller.get_system_status()
    assert status["app_name"] == "Vulcan Test OS"
    assert status["ollama"] == "Offline"

    caps = controller.get_registered_capabilities()
    assert "filesystem.read" in caps

    metrics = controller.get_ollama_metrics()
    assert metrics["status"] == "Offline"


def test_main_window_placeholder_initialization(qtbot: Any) -> None:
    controller = MockUIController()
    window = VulcanMainWindow(controller)
    qtbot.addWidget(window)

    assert window.windowTitle() == "VULCAN AI OPERATING SYSTEM — FOUNDATION ARCHITECTURE"
    status_msg = window.statusBar().currentMessage()
    assert "Operating System core booted in Phase 1 Orchestration Mode." in status_msg
