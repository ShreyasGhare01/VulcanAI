"""Visual identity and palette styling configuration for Vulcan AI OS."""

from PySide6.QtGui import QColor


def apply_dark_theme_palette() -> str:
    """Returns application wide QSS (Qt Style Sheet) rules and configures the standard palette

    to align cleanly with the requested spacecraft control room look.
    """
    charcoal = QColor("#1e1e24")  # Primary Background
    slate = QColor("#282a36")  # Secondary Panels / Header
    graphite = QColor("#383c4a")  # Elevated surface / inputs
    cool_gray = QColor("#5c6370")  # Borders
    off_white = QColor("#e5e9f0")  # Primary Text
    muted_gray = QColor("#888d96")  # Secondary Text

    qss = f"""
        QMainWindow {{
            background-color: {charcoal.name()};
        }}
        QDockWidget {{
            border: 1px solid {cool_gray.name()};
            background-color: {slate.name()};
            color: {off_white.name()};
        }}
        QDockWidget::title {{
            background-color: {slate.name()};
            padding: 6px;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
            border-bottom: 1px solid {cool_gray.name()};
        }}
        QTextEdit, QListView, QTreeView, QTableWidget, QScrollArea {{
            background-color: {graphite.name()};
            color: {off_white.name()};
            border: 1px solid {cool_gray.name()};
            font-family: 'Segoe UI', 'Noto Sans', 'Inter', sans-serif;
            font-size: 12px;
            padding: 4px;
        }}
        QLabel {{
            color: {off_white.name()};
            font-family: 'Segoe UI', 'Noto Sans', 'Inter', sans-serif;
            font-size: 12px;
        }}
        QStatusBar {{
            background-color: {slate.name()};
            color: {muted_gray.name()};
            border-top: 1px solid {cool_gray.name()};
            font-size: 11px;
        }}
    """
    return qss
