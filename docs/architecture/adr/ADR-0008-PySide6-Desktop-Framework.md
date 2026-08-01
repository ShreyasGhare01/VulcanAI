# ADR-0008: PySide6 Desktop Framework

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
To build a highly responsive and custom-dockable AI desktop experience, we need a robust UI framework. It must support timezone-aware hierarchical notifications, multi-monitor coordinates persistence, and custom styling.

### Decision
We select PySide6 (Qt for Python) as the official desktop presentation framework.
*   The presentation layer must remain extremely thin.
*   Visual coordinate states must be persisted on exit and restored on launch.
*   Blocking database or network operations must not execute on the main PySide6 thread.

### Alternatives Considered
*   **Electron / Web Interface**: Heavy, high memory usage, and doesn't integrate natively as a lightweight system utility without extensive overhead.
*   **Tkinter**: Lacks advanced dockable layouts and standard professional widgets.
*   **Flet (Flutter) / Custom Web Engine**: Lacks the mature desktop layout controls (like `QDockWidget` state saving) that make a multi-panel operating system interface cohesive.

### Consequences
*   **Easier**: We can leverage Qt's highly optimized native rendering, native menus, window docking states, and mature UI testing via `pytest-qt`.
*   **Harder**: Requires strict discipline to avoid importing Qt/PySide6 widgets or symbols in the Orchestration, Domain, or Infrastructure layers.

### Tradeoffs
We choose PySide6 for its top-tier desktop responsiveness and layout persistence, accepting that compiling and managing Qt dependencies requires careful pre-commit testing.

### Future Considerations
We can build a secondary CLI or Web-dashboard interface later because our domain logic is fully decoupled from the Presentation layer.

### Related ADRs
*   ADR-0002: Layered Architecture
*   ADR-0015: Modular UI with Dockable Panels

### References
*   `vulcan/ui/`
*   `tests/test_ui.py`
