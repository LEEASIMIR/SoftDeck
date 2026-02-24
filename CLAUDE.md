# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

SteamDeckSoft is a Windows-only PyQt6 desktop app that acts as a configurable button deck (similar to Stream Deck). It presents a grid of customizable buttons that can launch apps, send hotkeys, input text macros, control media, monitor system stats, and navigate between folders. Buttons are organized in an infinitely nestable folder tree structure, navigated via a toggleable left-side tree panel. It runs as a single-instance frameless always-on-top resizable window with a system tray icon, adjustable opacity, and supports a global hotkey to toggle visibility.

## Running

```bash
python main.py
```

Dependencies: `pip install -r requirements.txt` (requires Windows — uses pywin32, pycaw, comtypes, keyboard).

## Architecture

**Entry flow:** `main.py` → `src/app.py:SteamDeckSoftApp` (subclasses QApplication). The app enforces single-instance via QSharedMemory, sets up config/actions/services/UI, applies the dark theme, and calls `setQuitOnLastWindowClosed(False)` for tray-only operation.

**Initialization order in `SteamDeckSoftApp.__init__`:**
1. Single-instance check (QSharedMemory)
2. Logging setup
3. `ConfigManager` load
4. `ActionRegistry` + action registration
5. `InputDetector` start
6. `MainWindow` construction
7. `TrayIcon` construction
8. Background services start (`SystemStatsService`, optionally `ActiveWindowMonitor`)
9. `GlobalHotkeyService` start
10. Dark theme applied, window shown only if Num Lock is OFF (Num Lock ON → start hidden)

**Five main subsystems:**

1. **Config** (`src/config/`) — Dataclass-based models (`AppConfig` v2 → `AppSettings` + `FolderConfig` (recursive tree) → `ButtonConfig[]` → `ActionConfig`). `FolderConfig` supports infinite nesting via `children: list[FolderConfig]`. `ConfigManager` handles load/save with atomic writes (tmp file + `shutil.move`), plus `export_config(path)`/`import_config(path)` for JSON file export/import. User config lives at `%APPDATA%/SteamDeckSoft/config.json`, falling back to `config/default_config.json`. Automatic v1→v2 migration converts flat `pages` list to `root_folder` tree. `AppSettings` includes `global_hotkey` (default `"ctrl+\`"`), `window_opacity` (0.2–1.0, default 0.9), `folder_tree_visible` (default `True`).

2. **Actions** (`src/actions/`) — Plugin-like system. `ActionBase` is the ABC with `execute(params)` and `get_display_text(params)`. `ActionRegistry` maps string type names to action instances and holds an optional `main_window` reference for `NavigateFolderAction`. Current types: `launch_app`, `hotkey`, `text_input`, `media_control`, `system_monitor`, `navigate_folder` (+ `navigate_page` alias for backward compat). To add a new action: subclass `ActionBase`, register it in `SteamDeckSoftApp._register_actions()`.

3. **Services** (`src/services/`) — Background workers:
   - `SystemStatsService(QThread)` — polls CPU/RAM via psutil, emits `stats_updated(float, float)`
   - `ActiveWindowMonitor(QThread)` — polls foreground window via win32gui/win32process, emits `active_app_changed(str)` to drive auto-folder-switching
   - `MediaControlService` — wraps pycaw `IAudioEndpointVolume` COM interface for volume control (not a QThread, plain helper)
   - `GlobalHotkeyService(QObject)` — registers system-wide hotkey via `keyboard` library, emits `triggered` signal connected to `MainWindow.toggle_visibility`. Supports live rebinding via `update_hotkey()`
   - `InputDetector` — plain Python class using `ctypes` Win32 `WH_KEYBOARD_LL` hook in a daemon thread to detect injected (software-generated) keystrokes. Exposes `last_was_injected: bool`, used by `MainWindow.keyPressEvent` to prevent recursive triggering from `keyboard.send()`. Also detects Num Lock toggles and emits `numpad_signal.numlock_changed(bool)` to drive window visibility (Num Lock ON → hide, OFF → show). Static method `is_numlock_on()` checks current state at startup.

4. **UI** (`src/ui/`) — Frameless `MainWindow` with custom `TitleBar` (defined in `main_window.py`, provides drag support + folder tree toggle button + opacity slider + minimize/tray/quit buttons + right-click context menu with Settings / Export Config / Import Config). Window supports 8-direction edge drag resize (`_Edge` IntFlag + `_EDGE_CURSORS` mapping, 6px margin detection). Layout: `QVBoxLayout(TitleBar + QSplitter(FolderTreeWidget | GridContainer))`. `FolderTreeWidget` (in `folder_tree.py`) is a `QTreeWidget` showing the recursive folder structure with drag-and-drop reordering and right-click context menu (New Sub-Folder / Rename / Edit / Delete). `QGridLayout` of `DeckButton` widgets with 5 cycling color themes. Buttons are right-click editable via `ButtonEditorDialog` (uses `QStackedWidget` per action type; includes `HotkeyRecorderWidget` for keyboard capture with `grabKeyboard()`); button context menu also supports Copy/Paste to duplicate button configs across positions. Non-root folders auto-generate a "← Back" button at position `(0, 0)` that navigates to the parent folder (dynamic, not saved to config). Folders managed via `FolderEditorDialog`. Settings via `SettingsDialog` (includes opacity slider). `TrayIcon` provides show/settings/quit context menu and double-click to show.

5. **Styles** (`src/ui/styles.py`) — Dark theme with accent colors `#e94560`, `#533483`, `#0f3460`, background `#1a1a2e`. Exports `DARK_THEME`, `DECK_BUTTON_STYLE` (template with `{bg}/{hover}/{pressed}`), `DECK_BUTTON_EMPTY_STYLE`, `MONITOR_BUTTON_STYLE`, `FOLDER_TREE_STYLE`, `TITLE_BAR_STYLE`.

**Key data flow:** Config defines a root folder tree → each folder has `buttons` and `children` (sub-folders) → the grid shows the current folder's buttons → each button has an `ActionConfig(type, params)` → on click, `ActionRegistry.execute(type, params)` dispatches to the matching `ActionBase` subclass → services feed live data back to the UI via Qt signals. The folder tree panel allows navigation between folders; clicking a folder loads its buttons into the grid. Non-root folders dynamically inject a "← Back" button at `(0, 0)` to navigate to the parent folder. Buttons can be copied/pasted via `DeckButton._clipboard` (class-level dict storing `ButtonConfig.to_dict()` data).

**Keyboard shortcuts:** Global numpad keys (Num Lock OFF, via `InputDetector` hook) map numpad-layout keys (7-8-9/4-5-6/1-2-3) to grid positions `(row, col)` in the top-left 3x3 area.

**Window behavior:** `closeEvent` minimizes to tray instead of quitting. `toggle_visibility` hides to tray or `show_on_primary()` (centers on primary screen top edge). Window uses `setMinimumSize` (not `setFixedSize`) to allow drag resize. `set_opacity(value)` applies opacity and persists to config. TitleBar has a horizontal `QSlider` (20–100%) for real-time opacity control. **Num Lock–driven visibility:** Num Lock ON hides the window, Num Lock OFF shows it. This is checked both at startup and on every Num Lock toggle via `InputDetector`.

## Conventions

- All modules use `from __future__ import annotations` and `TYPE_CHECKING` guards for type-only imports
- Private attributes prefixed with `_`; no public setters except through property accessors
- Qt signals/slots for all cross-component communication
- Button positions are `(row, col)` tuples
- Config uses `to_dict()`/`from_dict()` pattern (no Pydantic)
- Dialogs use lazy imports to avoid circular dependencies
- Services are injected via setter methods (e.g., `set_main_window()`, `set_media_service()`, `set_input_detector()`)
- New folder IDs use `uuid.uuid4().hex[:8]`
- Config version is 2; v1 configs are auto-migrated on load

## File Map

```
main.py                          # Entry point
src/app.py                       # SteamDeckSoftApp — orchestrates everything
src/config/models.py             # Dataclasses: AppConfig, AppSettings, FolderConfig, ButtonConfig, ActionConfig (+ deprecated PageConfig for migration)
src/config/manager.py            # ConfigManager — load/save with atomic writes + folder CRUD + export/import
src/actions/base.py              # ActionBase ABC
src/actions/registry.py          # ActionRegistry — type→action dispatch + main_window ref
src/actions/launch_app.py        # LaunchAppAction — subprocess.Popen / os.startfile fallback
src/actions/hotkey.py            # HotkeyAction — keyboard.send()
src/actions/text_input.py        # TextInputAction — keyboard.write() or clipboard paste (win32clipboard + Ctrl+V)
src/actions/media.py             # MediaControlAction — volume via pycaw, media keys via keyboard
src/actions/navigate.py          # NavigateFolderAction — folder switching via registry.main_window
src/actions/system_monitor.py    # SystemMonitorAction — display-only, live data via DeckButton
src/services/system_stats.py     # SystemStatsService(QThread) — CPU/RAM polling
src/services/window_monitor.py   # ActiveWindowMonitor(QThread) — foreground window tracking
src/services/media_control.py    # MediaControlService — pycaw IAudioEndpointVolume wrapper
src/services/global_hotkey.py    # GlobalHotkeyService(QObject) — system-wide hotkey
src/services/input_detector.py   # InputDetector — Win32 keyboard hook for injected key detection
src/ui/main_window.py           # MainWindow + TitleBar — frameless resizable window, QSplitter(tree|grid), opacity slider
src/ui/button_widget.py         # DeckButton(QPushButton) — colored buttons with context menu (edit/clear/copy/paste)
src/ui/folder_tree.py           # FolderTreeWidget(QTreeWidget) — left panel folder tree with drag-and-drop
src/ui/folder_editor_dialog.py  # FolderEditorDialog — name + mapped apps list for folders
src/ui/button_editor_dialog.py  # ButtonEditorDialog — per-action-type stacked editor + HotkeyRecorderWidget
src/ui/settings_dialog.py       # SettingsDialog — grid/behavior/appearance settings
src/ui/styles.py                # All style constants
src/ui/tray_icon.py             # TrayIcon(QSystemTrayIcon) — system tray with context menu
config/default_config.json       # Default 3x3 grid with 9 hotkey buttons (v2 format)
```
