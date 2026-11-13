# Vulcan Developer Setup & Contribution Guide

This guide helps contributors boot up, run, and test the Vulcan AI Operating System.

---

## 1. Quick Setup

### Prerequisites
- Python 3.12 or higher.
- [Ollama](https://ollama.com) running locally.

### Installation
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
ollama pull qwen3:4b
```

### Choosing the local model
The default model is `qwen3:4b`, sized for CPU-only machines. To use another model, set
`VULCAN_MODEL_DEFAULT_MODEL` (e.g. `qwen3:1.7b` for faster replies on slower hardware).
Vulcan asks Qwen3 to answer without its "thinking" pass; set `VULCAN_MODEL_DISABLE_THINKING=false`
to turn that off.

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
