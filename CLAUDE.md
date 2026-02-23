# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

SteamDeckSoft is a Windows-only PyQt6 desktop app that acts as a configurable button deck (similar to Stream Deck). It presents a grid of customizable buttons that can launch apps, send hotkeys, control media, monitor system stats, and navigate between pages. It runs as a single-instance frameless always-on-top window with a system tray icon.

## Running

```bash
python main.py
```

Dependencies: `pip install -r requirements.txt` (requires Windows — uses pywin32, pycaw, comtypes).

## Architecture

**Entry flow:** `main.py` → `src/app.py:SteamDeckSoftApp` (subclasses QApplication). The app enforces single-instance via QSharedMemory, sets up config/actions/services/UI, and applies the dark theme.

**Four main subsystems:**

1. **Config** (`src/config/`) — Dataclass-based models (`AppConfig` → `AppSettings` + `PageConfig[]` → `ButtonConfig[]` → `ActionConfig`). `ConfigManager` handles load/save with JSON serialization. User config lives at `%APPDATA%/SteamDeckSoft/config.json`, falling back to `config/default_config.json`.

2. **Actions** (`src/actions/`) — Plugin-like system. `ActionBase` is the ABC with `execute(params)` and `get_display_text(params)`. `ActionRegistry` maps string type names to action instances. Current types: `launch_app`, `hotkey`, `media_control`, `system_monitor`, `navigate_page`. To add a new action: subclass `ActionBase`, register it in `SteamDeckSoftApp._register_actions()`.

3. **Services** (`src/services/`) — Background QThread workers. `SystemStatsService` polls CPU/RAM via psutil, emits `stats_updated`. `ActiveWindowMonitor` polls the foreground window via win32gui, emits `active_app_changed` to drive auto-page-switching. `MediaControlService` wraps pycaw for volume control (not a QThread, just a helper).

4. **UI** (`src/ui/`) — Frameless `MainWindow` with custom `TitleBar` (drag support), a `QGridLayout` of `DeckButton` widgets, and a `PageBar` at the bottom. Buttons are right-click editable via `ButtonEditorDialog`. Pages are managed via `PageEditorDialog`. Settings via `SettingsDialog`. All styles in `styles.py` (dark theme with accent colors `#e94560`, `#533483`, `#0f3460`).

**Key data flow:** Config defines pages of buttons → each button has an `ActionConfig(type, params)` → on click, `ActionRegistry.execute(type, params)` dispatches to the matching `ActionBase` subclass → services feed live data back to the UI via Qt signals.

## Conventions

- All modules use `from __future__ import annotations` and `TYPE_CHECKING` guards for type-only imports
- Private attributes prefixed with `_`; no public setters except through property accessors
- Qt signals/slots for all cross-component communication
- Button positions are `(row, col)` tuples
- Config uses `to_dict()`/`from_dict()` pattern (no Pydantic)
- Dialogs use lazy imports to avoid circular dependencies
