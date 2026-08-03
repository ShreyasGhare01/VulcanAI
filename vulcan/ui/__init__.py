"""Presentation Layer package.

Responsibility:
    Responsible for PySide6 desktop visualization rendering, customizable dock card widgets,
    and responsive application themes. Uses controllers to communicate with background
    orchestration layers safely off the UI thread.

Dependencies:
    - PySide6, Qt libraries
    - vulcan/config/ (VulcanConfig)
    - vulcan/core/ (CapabilityRegistry)
    - vulcan/services/ (IInferenceProvider)

Public Interfaces:
    - VulcanMainWindow
    - UIController

Forbidden Dependencies:
    - No background database drivers, LLM endpoints, or vector search clients may be imported here.
    - All operational commands must flow through the controller layer.
"""
