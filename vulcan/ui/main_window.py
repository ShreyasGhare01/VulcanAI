"""Main Application Window shell displaying 11 dockable panels with dark spacecraft theme."""

from typing import Any

from PySide6.QtCore import QByteArray, QSettings, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from vulcan.ui.controller import MockUIController, UIController
from vulcan.ui.theme import apply_dark_theme_palette


class CognitiveWorker(QThread):
    """Asynchronous background worker to process Cognitive Loop executions safely off the GUI thread."""

    finished_signal = Signal(str, dict, dict, list)

    def __init__(self, controller: Any, user_input: str):
        super().__init__()
        self.controller = controller
        self.user_input = user_input

    def run(self) -> None:
        try:
            # Process complete loop execution safely in the background
            result = self.controller.send_message(self.user_input)
        except Exception as e:
            result = f"Error processing cognitive loop: {e}"

        # Fetch status updates
        sys_status = self.controller.get_system_status()
        model_metrics = self.controller.get_ollama_metrics()

        # Accumulate events (For simulation/mock display when backend event lists are offline)
        events_captured = []
        if self.controller.cognitive_router and hasattr(
            self.controller.cognitive_router.event_bus, "_subscribers"
        ):
            # Simply report recent simulated completion logs
            events_captured = [
                "Session.Created",
                "Inference.Started",
                "Planning.Completed",
                "Inference.Completed",
                "Response.Generated",
            ]
        else:
            events_captured = ["Inference.Started", "Response.Generated"]

        self.finished_signal.emit(result, sys_status, model_metrics, events_captured)


class VulcanMainWindow(QMainWindow):
    """The polished main workspace for the Vulcan AI OS.

    Renders 11 fully dockable widgets, and supports state persist/restore.
    """

    state_changed_signal = Signal(str)

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

        # Wire up Cognitive Loop state listener for developer Mode visualization
        self.state_changed_signal.connect(self._handle_state_changed)
        if hasattr(self.controller, "cognitive_router") and self.controller.cognitive_router:
            self.controller.cognitive_router.event_bus.subscribe(
                "Cognition.StateChanged", self._on_bus_state_changed
            )

    def _on_bus_state_changed(self, event: Any) -> None:
        """Executed on Event Bus worker thread. Safely emits signal to the UI thread."""
        state = event.data.get("state", "Idle")
        self.state_changed_signal.emit(state)

    @Slot(str)  # type: ignore[untyped-decorator]
    def _handle_state_changed(self, state: str) -> None:
        """Main UI Thread slot updating the visual layout with state change status."""
        self.statusBar().showMessage(f"Thinking [State: {state}]...")
        self.dev_text.append(f"Cognitive Loop State: {state} ✓")

    def _create_dock_card(self, title: str, inner_widget: QWidget) -> QDockWidget:
        """Helper to encapsulate widgets inside QDockWidgets."""
        dock = QDockWidget(title, self)
        dock.setObjectName(f"dock_{title.lower().replace(' ', '_')}")
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        dock.setWidget(inner_widget)
        return dock

    def _init_dock_widgets(self) -> None:
        """Configures and registers 11 core docking cards."""
        # 1. Conversation Panel (Functionalized)
        conv_container = QWidget()
        conv_layout = QVBoxLayout(conv_container)
        conv_layout.setContentsMargins(5, 5, 5, 5)

        self.conv_text = QTextEdit()
        self.conv_text.setReadOnly(True)
        self.conv_text.setPlaceholderText(">> System is listening. Input instructions...")
        conv_layout.addWidget(self.conv_text)

        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask Vulcan or issue terminal commands...")
        self.input_box.returnPressed.connect(self._handle_send_message)
        input_layout.addWidget(self.input_box)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._handle_send_message)
        input_layout.addWidget(self.send_button)
        conv_layout.addLayout(input_layout)

        dock_conv = self._create_dock_card("Conversation", conv_container)
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
        self.sys_widget = QWidget()
        self.sys_layout = QVBoxLayout(self.sys_widget)
        self.sys_layout.setContentsMargins(10, 10, 10, 10)
        self.sys_layout.setSpacing(6)
        self._refresh_system_status_labels(self.controller.get_system_status())

        dock_sys = self._create_dock_card("System Status", self.sys_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_sys)

        # 6. Event Log Panel
        self.event_text = QTextEdit()
        self.event_text.setReadOnly(True)
        self.event_text.setPlaceholderText("Subscribing to system Event Bus...")
        dock_event = self._create_dock_card("Event Log", self.event_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_event)

        # 7. Notifications Panel
        notif_text = QTextEdit()
        notif_text.setReadOnly(True)
        notif_text.setPlaceholderText("No unread alerts.")
        dock_notif = self._create_dock_card("Notifications", notif_text)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_notif)

        # 8. Development Activity Panel
        self.dev_text = QTextEdit()
        self.dev_text.setReadOnly(True)
        self.dev_text.setPlaceholderText(
            "Development capabilities are unmapped. Execution activity logs here."
        )
        dock_dev = self._create_dock_card("Development Activity", self.dev_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_dev)

        # 9. Settings Panel
        settings_text = QTextEdit()
        settings_text.setReadOnly(True)
        settings_text.setPlaceholderText("Default config loaded. Priority sequence active.")
        dock_settings = self._create_dock_card("Settings", settings_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_settings)

        # 10. Model Status Panel
        self.model_widget = QWidget()
        self.model_layout = QVBoxLayout(self.model_widget)
        self.model_layout.setContentsMargins(10, 10, 10, 10)
        self.model_layout.setSpacing(6)
        self._refresh_model_status_labels(self.controller.get_ollama_metrics())

        dock_model = self._create_dock_card("Model Status", self.model_widget)
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

    def _refresh_system_status_labels(self, sys_data: dict[str, Any]) -> None:
        """Clears and re-adds system status metrics."""
        # Clear old items
        for i in reversed(range(self.sys_layout.count())):
            item = self.sys_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        for k, v in sys_data.items():
            label = QLabel(f"<b>{k.replace('_', ' ').title()}:</b> {v}")
            self.sys_layout.addWidget(label)
        self.sys_layout.addStretch()

    def _refresh_model_status_labels(self, model_metrics: dict[str, Any]) -> None:
        """Clears and re-adds model latency/statistics labels."""
        # Clear old items
        for i in reversed(range(self.model_layout.count())):
            item = self.model_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        for k, v in model_metrics.items():
            label = QLabel(f"<b>{k.replace('_', ' ').title()}:</b> {v}")
            self.model_layout.addWidget(label)
        self.model_layout.addStretch()

    def _init_status_bar(self) -> None:
        self.statusBar().showMessage(
            "Ready — Operating System core booted in Phase 1 Orchestration Mode."
        )

    def _restore_saved_state(self) -> None:
        """Restores window coordinates and layouts using QSettings."""
        settings = QSettings("VulcanOrg", "VulcanAI")
        geom = settings.value("geometry")
        state = settings.value("windowState")

        if isinstance(geom, QByteArray):
            self.restoreGeometry(geom)
        if isinstance(state, QByteArray):
            self.restoreState(state)

    def _handle_send_message(self) -> None:
        """Extracts user input, updates history, and safely schedules background processing."""
        text = self.input_box.text().strip()
        if not text:
            return

        self.input_box.clear()
        self.conv_text.append(f"\n<b>User:</b> {text}")
        self.statusBar().showMessage("Thinking...")

        # Disable send interface while processing to avoid double execution
        self.send_button.setEnabled(False)
        self.input_box.setEnabled(False)

        # Kick off safe off-thread background processing
        self.worker = CognitiveWorker(self.controller, text)
        self.worker.finished_signal.connect(self._handle_cognitive_loop_complete)
        self.worker.start()

    @Slot(str, dict, dict, list)  # type: ignore[untyped-decorator]
    def _handle_cognitive_loop_complete(
        self,
        result: str,
        sys_status: dict[str, Any],
        model_metrics: dict[str, Any],
        events: list[str],
    ) -> None:
        """Handles background task completion, rendering text, events, and refreshed stats."""
        # Display assistant reply
        self.conv_text.append(f"<b>Assistant:</b> {result}")
        self.statusBar().showMessage("Ready")

        # Re-enable inputs
        self.send_button.setEnabled(True)
        self.input_box.setEnabled(True)
        self.input_box.setFocus()

        # Update diagnostic metrics labels
        self._refresh_system_status_labels(sys_status)
        self._refresh_model_status_labels(model_metrics)

        # Display Planner Decisions and executions inside Development Activity
        self.dev_text.append(
            f"\n[Planner Decision ID] Generated action loop feedback: {result[:120]}..."
        )

        # Display captured Events inside the Event Log Panel
        for ev in events:
            self.event_text.append(f"[{ev}] published to Hierarchical Event Bus.")

    def closeEvent(self, event: Any) -> None:
        """Saves current dock placement coordinates on close."""
        settings = QSettings("VulcanOrg", "VulcanAI")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)
