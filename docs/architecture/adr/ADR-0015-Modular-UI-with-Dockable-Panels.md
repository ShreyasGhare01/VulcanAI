# ADR-0015: Modular UI with Dockable Panels

### Status
Accepted

### Date
2025-02-15

### Authors
Vulcan Core Team & Jules

---

### Context
An AI operating system coordinates many visual tools simultaneously (e.g., chat histories, active task trees, file editors, memory vectors, and real-time logs). A rigid, static layout cannot accommodate all these views comfortably, especially across different screen sizes.

### Decision
The desktop UI (built with PySide6) is strictly required to use `QDockWidget` objects to support customizable, dockable panels.
*   Users can drag, resize, undock, stack, or collapse specific panels.
*   We utilize Qt's native `saveState()` and `restoreState()` mechanisms to persist layout configurations on application close and restore them on subsequent launches.

### Alternatives Considered
*   **Static Grid Layouts**: Unbelievably rigid; forces the user into a single layout that cannot be customized for complex multi-monitor workspaces.
*   **Single-Panel Tabbed Interface**: Keeps important information hidden behind tabs, preventing simultaneous monitoring of real-time logs and conversation feeds.

### Consequences
*   **Easier**: Infinite user layout customization, clean visual isolation of sub-panels, and native desktop window management.
*   **Harder**: Requires designing widgets to handle dynamic resizing gracefully and coordinate layout states safely inside the UI controller.

### Tradeoffs
We accept the minor layout management complexity of `QDockWidget` to deliver a professional, multi-panel operating system interface.

### Future Considerations
This lets developers easily add new visual panels (such as a performance monitor or neural network visualizer) as dockable widgets without disrupting existing UI components.

### Related ADRs
*   ADR-0008: PySide6 Desktop Framework

### References
*   `tests/test_ui.py`
