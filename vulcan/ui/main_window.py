"""Main Application Window shell displaying 11 dockable panels with dark spacecraft theme."""

from typing import Any

from PySide6.QtCore import QByteArray, QSettings, Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QLabel,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from vulcan.ui.controller import MockUIController, UIController
from vulcan.ui.theme import apply_dark_theme_palette


class VulcanMainWindow(QMainWindow):
    """The polished main workspace for the Vulcan AI OS.

    Renders 11 fully dockable widgets, and supports state persist/restore.
    """

    def __init__(self, controller: UIController | MockUIController):
        super().__init__()
        self.controller = controller

        self.setWindowTitle("VULCAN AI OPERATING SYSTEM — FOUNDATION ARCHITECTURE")
        self.resize(1200, 800)

        # Apply visual styling and palette
        self.setStyleSheet(apply_dark_theme_palette())

        self.setDockOptions(
            QMainWindow.DockOption.AnimatedDocks | QMainWindow.DockOption.AllowTabbedDocks
        )

        # Build placeholders
        self._init_dock_widgets()

        # Create status bar
        self._init_status_bar()

        # Try to restore layout if saved in previous session
        self._restore_saved_state()

    def _create_dock_card(self, title: str, inner_widget: QWidget) -> QDockWidget:
        """Helper to encapsulate widgets inside QDockWidgets."""
        dock = QDockWidget(title, self)
        dock.setObjectName(f"dock_{title.lower().replace(' ', '_')}")
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        dock.setWidget(inner_widget)
        return dock

    def _init_dock_widgets(self) -> None:
        """Configures and registers 11 core docking cards."""
        # 1. Conversation Panel
        conv_text = QTextEdit()
        conv_text.setReadOnly(True)
        conv_text.setPlaceholderText(">> System is listening. Input instructions...")
        dock_conv = self._create_dock_card("Conversation", conv_text)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_conv)

        # 2. Active Tasks Panel
        tasks_text = QTextEdit()
        tasks_text.setReadOnly(True)
        tasks_text.setPlaceholderText("No active tasks running.")
        dock_tasks = self._create_dock_card("Active Tasks", tasks_text)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_tasks)

        # 3. Running Agents Panel
        agents_text = QTextEdit()
        agents_text.setReadOnly(True)
        agents_text.setPlaceholderText("No autonomous agents currently executing.")
        dock_agents = self._create_dock_card("Running Agents", agents_text)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_agents)

        # 4. Memory Timeline Panel
        mem_text = QTextEdit()
        mem_text.setReadOnly(True)
        mem_text.setPlaceholderText("Memory streams are unmapped. Core database offline.")
        dock_mem = self._create_dock_card("Memory Timeline", mem_text)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_mem)

        # 5. System Status Panel
        sys_widget = QWidget()
        sys_layout = QVBoxLayout(sys_widget)
        sys_layout.setContentsMargins(10, 10, 10, 10)
        sys_layout.setSpacing(6)

        sys_data = self.controller.get_system_status()
        for k, v in sys_data.items():
            label = QLabel(f"<b>{k.replace('_', ' ').title()}:</b> {v}")
            sys_layout.addWidget(label)
        sys_layout.addStretch()

        dock_sys = self._create_dock_card("System Status", sys_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_sys)

        # 6. Event Log Panel
        event_text = QTextEdit()
        event_text.setReadOnly(True)
        event_text.setPlaceholderText("Subscribing to system Event Bus...")
        dock_event = self._create_dock_card("Event Log", event_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_event)

        # 7. Notifications Panel
        notif_text = QTextEdit()
        notif_text.setReadOnly(True)
        notif_text.setPlaceholderText("No unread alerts.")
        dock_notif = self._create_dock_card("Notifications", notif_text)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_notif)

        # 8. Development Activity Panel
        dev_text = QTextEdit()
        dev_text.setReadOnly(True)
        dev_text.setPlaceholderText("Development capabilities are unmapped.")
        dock_dev = self._create_dock_card("Development Activity", dev_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_dev)

        # 9. Settings Panel
        settings_text = QTextEdit()
        settings_text.setReadOnly(True)
        settings_text.setPlaceholderText("Default config loaded. Priority sequence active.")
        dock_settings = self._create_dock_card("Settings", settings_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_settings)

        # 10. Model Status Panel
        model_widget = QWidget()
        model_layout = QVBoxLayout(model_widget)
        model_layout.setContentsMargins(10, 10, 10, 10)
        model_layout.setSpacing(6)

        model_metrics = self.controller.get_ollama_metrics()
        for k, v in model_metrics.items():
            label = QLabel(f"<b>{k.replace('_', ' ').title()}:</b> {v}")
            model_layout.addWidget(label)
        model_layout.addStretch()

        dock_model = self._create_dock_card("Model Status", model_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_model)

        # 11. Skill Registry Panel
        skills_widget = QWidget()
        skills_layout = QVBoxLayout(skills_widget)
        skills_layout.setContentsMargins(10, 10, 10, 10)
        skills_layout.setSpacing(6)

        caps = self.controller.get_registered_capabilities()
        if caps:
            for cap, providers in caps.items():
                label = QLabel(f"• <b>{cap}</b> (by {', '.join(providers)})")
                skills_layout.addWidget(label)
        else:
            label = QLabel("No active capabilities registered.")
            skills_layout.addWidget(label)
        skills_layout.addStretch()

        dock_skills = self._create_dock_card("Skill Registry", skills_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_skills)

        # Distribute into tabbed overlays to minimize clutter
        self.tabifyDockWidget(dock_conv, dock_tasks)
        self.tabifyDockWidget(dock_tasks, dock_agents)

        self.tabifyDockWidget(dock_sys, dock_model)
        self.tabifyDockWidget(dock_model, dock_skills)
        self.tabifyDockWidget(dock_skills, dock_mem)
        self.tabifyDockWidget(dock_mem, dock_notif)

        self.tabifyDockWidget(dock_event, dock_dev)
        self.tabifyDockWidget(dock_dev, dock_settings)

    def _init_status_bar(self) -> None:
        self.statusBar().showMessage("Ready — Operating System core booted in Phase 0 Mode.")

    def _restore_saved_state(self) -> None:
        """Restores window coordinates and layouts using QSettings."""
        settings = QSettings("VulcanOrg", "VulcanAI")
        geom = settings.value("geometry")
        state = settings.value("windowState")

        if isinstance(geom, QByteArray):
            self.restoreGeometry(geom)
        if isinstance(state, QByteArray):
            self.restoreState(state)

    def closeEvent(self, event: Any) -> None:
        """Saves current dock placement coordinates on close."""
        settings = QSettings("VulcanOrg", "VulcanAI")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)
