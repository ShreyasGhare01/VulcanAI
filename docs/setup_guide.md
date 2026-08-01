# Vulcan Developer Setup & Contribution Guide

This guide helps contributors boot up, run, and test the Vulcan AI Operating System.

---

## 1. Quick Setup

### Prerequisites
- Python 3.12 or higher.

### Installation
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
```

---

## 2. Code Quality & Standards

We enforce strict validation prior to every submission:

- **Formatting (Black)**:
  ```bash
  black vulcan/ tests/
  ```
- **Linting (Ruff)**:
  ```bash
  ruff check vulcan/ tests/ --fix
  ```
- **Static Typing (MyPy)**:
  ```bash
  mypy vulcan/ tests/
  ```
- **Automated Tests (Pytest)**:
  ```bash
  PYTHONPATH=. QT_QPA_PLATFORM=offscreen pytest tests/
  ```
