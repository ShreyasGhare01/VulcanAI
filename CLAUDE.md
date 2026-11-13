# CLAUDE.md — VulcanAI

This file is the working guide for Claude Code in this repo. For the full background, see the "VulcanAI — Project Context" doc in the claude.ai project.

## What this is

Vulcan is a personal Jarvis-style assistant. It has a Python core (cognitive loop + memory) and runs a local Qwen3 model through Ollama for everyday chat. Claude handles harder tasks. The interface is moving from PySide6 to a browser HUD (red and black) ported from adewaskar/jarvis.

## Setup and checks (Windows, PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
ollama pull qwen3:4b

# tests (headless Qt)
$env:QT_QPA_PLATFORM="offscreen"; pytest tests/

ruff check vulcan/ tests/
black --check vulcan/ tests/
mypy vulcan/
```

Run the tests and ruff before saying a change is done.

## Layout

- `vulcan/core/`: bootstrap, DI container, event bus, command bus, capability registry
- `vulcan/cognition/`: router (the cognitive loop), planner, context pipeline, prompt builder, sessions
- `vulcan/memory/`: MemoryManager, Memory Council, SQLite store, Obsidian vault, Chroma
- `vulcan/services/`: Ollama inference provider, Chroma client
- `vulcan/skills/`: skill packages (`manifest.json` + code)
- `vulcan/ui/`: PySide6 UI (**being retired**: don't extend it)
- `docs/architecture/`: Constitution, specs, ADRs

## How to work (Karpathy guidelines)

1. **Think before coding.** Read the relevant code and say your plan before editing. If the request is ambiguous, ask.
2. **Simplicity first.** Write the smallest change that solves the problem. Add no abstractions, layers or config "for later."
3. **Surgical changes.** Touch only what the task needs. Don't reformat, rename or refactor unrelated code in the same change.
4. **Goal-driven execution.** Define what "done" looks like (a passing test, a working command), then work until it's verified.

## Rules

- **The hardware is CPU only** (no NVIDIA GPU). Every model call costs seconds.
  - Make one model call per user message.
  - Stream responses.
  - Run memory extraction in the background after the reply.
  - Turn Qwen3's thinking mode off for chat.
- **Never hard-code a model name.** Read it from `VulcanConfig`.
- **Respect the layers:** UI → cognition → memory/services → core. Memory must never import UI code.
- **Consequential actions need user approval**, enforced in the backend. Tools declare a permission category, and nothing is enabled by default.
- **Obsidian vault:** read freely, ask before editing, never delete.
- **Code borrowed from adewaskar/jarvis:** keep its MIT notice and record the source file and commit in `THIRD_PARTY_NOTICES.md`. Don't copy Jarvis's audio files.
- Keep docs honest: README and ROADMAP must describe what actually works.
- Write a new ADR only for a significant architectural decision.

## Current focus

Step 2: the Python bridge, a FastAPI + WebSocket server between the browser HUD and the cognitive loop. Step 1 (Phase 2 fixes) is done.

Known leftovers from Phase 2, not urgent:
- Replies don't stream to the UI yet. That comes with the bridge.
- `memory/manager.py` reaches into `sqlite_repo._get_connection()` directly.
- Failed pending extractions retry on every startup, with no attempt limit.
- `memory/council.py` isn't black-formatted.
- Pre-existing mypy errors in `ui/main_window.py` (PySide6, being retired).
