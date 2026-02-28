# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

SoftDeck is a Windows-only PyQt6 desktop app that acts as a configurable button deck (similar to Stream Deck). It presents a grid of customizable buttons that can launch apps, send hotkeys, input text macros, control media, monitor system stats, open URLs, run shell commands, and navigate between folders. Buttons are organized in an infinitely nestable folder tree structure, navigated via a toggleable left-side tree panel. It runs as a single-instance frameless always-on-top resizable window with a system tray icon and adjustable opacity. Visibility is driven by Num Lock state (OFF = show, ON = hide).

## Running

```bash
python main.py
```

Dependencies: `pip install -r requirements.txt` (requires Windows — uses pywin32, pycaw, comtypes, keyboard, winrt-Windows.Media.Control).

## Architecture

**Entry flow:** `main.py` checks single-instance via Win32 Named Mutex (`CreateMutexW`) **before any imports**, then → `src/app.py:SoftDeckApp` (subclasses QApplication). This prevents a second instance from importing `keyboard` or creating a QApplication, which could interfere with the first instance's Win32 keyboard hooks.

**Initialization order in `SoftDeckApp.__init__`:**
1. Logging setup (file log to `%APPDATA%/SoftDeck/app.log` + console if stdout exists)
2. Single-instance check (`_ensure_single_instance` — kills existing `softdeck.exe` via psutil if mutex already held, retries up to 5s)
3. `ConfigManager` load
4. Theme resolution (`get_theme(settings.theme)` → `ThemeStylesheets`)
5. `ToastManager` creation (themed toast notifications)
6. `ActionRegistry` + built-in action registration
7. `PluginLoader` discover + load → plugin actions registered into `ActionRegistry`
8. `InputDetector` start
9. `MainWindow` construction + service injection (`set_input_detector`, `set_toast_manager`)
10. `TrayIcon` construction
11. Background services start (`SystemStatsService`, optionally `ActiveWindowMonitor`, optionally `MediaPlaybackMonitor` from media plugin, mute state `QTimer` polling via `MediaControlService`)
12. Theme applied globally via `setStyleSheet`
13. Window shown only if Num Lock is OFF (Num Lock ON → start hidden)
14. Ready notification (themed toast + system sound)

**Seven main subsystems:**

1. **Config** (`src/config/`) — Dataclass-based models (`AppConfig` v2 → `AppSettings` + `FolderConfig` (recursive tree) → `ButtonConfig[]` → `ActionConfig`). `FolderConfig` supports infinite nesting via `children: list[FolderConfig]`. `FolderConfig.expanded` (bool, default `True`) tracks tree expand/collapse state. `ButtonConfig` includes per-button styling: `label_color` (hex string, default empty = white), `label_size` (int px, default 0 = use `AppSettings.default_label_size`). `ConfigManager` handles load/save with atomic writes (tmp file + `shutil.move`), plus `export_config(path)`/`import_config(path)` for JSON file export/import. User config lives at `%APPDATA%/SoftDeck/config.json`, falling back to `config/default_config.json`. Automatic v1→v2 migration converts flat `pages` list to `root_folder` tree. `AppSettings` fields: `grid_rows` (default 3), `grid_cols` (default 5), `button_size` (default 60px), `button_spacing` (default 8px), `default_label_size` (default 10px), `default_label_family` (font family, default empty), `auto_switch_enabled` (default `True`), `always_on_top` (default `True`), `theme` (default `"dark"`), `window_opacity` (0.2–1.0, default 0.9), `folder_tree_visible` (default `True`), `window_x`/`window_y` (last position, `None` = center-top). `AppConfig` stores `app_version` from `src/version.py` (`APP_VERSION = "0.1.0-beta"`); on load, version mismatch triggers re-save.

2. **Actions** (`src/actions/`) — `ActionBase` is the ABC with `execute(params)` and `get_display_text(params)`. `ActionRegistry` maps string type names to action instances and holds an optional `main_window` reference for `NavigateFolderAction`. Built-in types: `launch_app`, `hotkey`, `text_input`, `system_monitor`, `navigate_folder` (+ `navigate_page` alias for backward compat), `open_url`, `macro`, `run_command`. Plugin-provided types: `media_control` (via media_control plugin). `LaunchAppAction` uses `MainWindow.launch_with_foreground()` wrapper around `os.startfile()` (ensures launched app window gets foreground) with `subprocess.Popen(CREATE_NEW_CONSOLE)` fallback when arguments are provided. `HotkeyAction` has `_SPECIAL_HOTKEYS` dict (lazily initialized via `_init_special()`) for Windows-protected shortcuts (e.g., `win+l` → `LockWorkStation()` API). `TextInputAction` supports `use_clipboard` mode — when True, copies text to clipboard via `win32clipboard` and pastes with `Ctrl+V` instead of using `keyboard.write()`. `OpenUrlAction` uses `os.startfile()` (Windows shell default browser). To add a new action: create a plugin (see Plugins subsystem) or subclass `ActionBase` and register in `SoftDeckApp._register_actions()`.

3. **Services** (`src/services/`) — Background workers:
   - `SystemStatsService(QThread)` — polls CPU/RAM via psutil, emits `stats_updated(float, float)`
   - `ActiveWindowMonitor(QThread)` — polls foreground window via win32gui/win32process, emits `active_app_changed(str)` to drive auto-folder-switching
   - `InputDetector` — launches `numpad_hook.dll` in a separate `rundll32.exe` process and communicates via named shared memory (`Local\SoftDeck_NumpadHook`). Polls events from a lock-free ring buffer via `QTimer` at 16ms (~60Hz). Detects Num Lock toggles and emits `numpad_signal.numlock_changed(bool)` to drive window visibility (Num Lock ON → hide, OFF → show). Numpad scan codes 71–73/75–77/79–81 map to grid positions `(row, col)` in the 3x3 area; scan 82 (Numpad 0 = Insert when Num Lock OFF) emits `numpad_signal.back_pressed` → `MainWindow.navigate_back()`. Static method `is_numlock_on()` checks current state at startup. Has `_passthrough` flag toggled via `set_passthrough(bool)` — when True, numpad keys pass through (used when dialogs are open). Passes `os.getpid()` to rundll32 so the DLL auto-exits if the parent process crashes.

4. **UI** (`src/ui/`) — Frameless `MainWindow` with custom `TitleBar` (defined in `main_window.py`, provides drag support + folder tree toggle button + current folder name label (centered) + opacity slider + tray button + right-click context menu with Settings / Export Config / Import Config). TitleBar height is 25px with top-aligned layout; folder name is updated via `TitleBar.update_folder_name()` whenever `_load_current_folder()` runs. Window supports 8-direction edge drag resize (`_Edge` IntFlag + `_EDGE_CURSORS` mapping, 6px margin detection). Layout: `QVBoxLayout(TitleBar + QSplitter(FolderTreeWidget | GridContainer) + VersionLabel)`. `FolderTreeWidget` (in `folder_tree.py`) is a `QTreeWidget` showing the recursive folder structure with drag-and-drop reordering and right-click context menu (New Sub-Folder / Rename / Edit / Delete). `QGridLayout` of `DeckButton` widgets. `DeckButton` overrides `paintEvent` when an icon is set: draws button background → icon (full opacity, centered) → label text on top, applying per-button `label_color` and `label_size`. If a button has an icon and its label is empty, text is hidden (icon-only display). **Icon priority:** per-state toggle icon (`ActionConfig.params` `play_icon`/`pause_icon`/`mute_icon`/`unmute_icon`) > per-button custom icon (`ButtonConfig.icon`) > default action icon (`assets/icons/actions/`) > plugin icon (`PluginBase.get_icon_path()`) > no icon (text only). **Media toggle buttons** (`play_pause`, `mute`) support per-state icons and labels stored in `ActionConfig.params`; when a per-state label is set without a per-state icon, default icons are suppressed for text-only display. `DeckButton` tracks `_media_is_playing` and `_media_is_muted` flags; shared update logic in `_update_media_toggle()` via `_MEDIA_TOGGLE_KEYS` dict maps each toggle command to its active/inactive param key pairs. Default icons resolved by `default_icons.py`: built-in action types map to `assets/icons/actions/{type}.png`; plugin icons fall through to `_plugin_icon_resolver` callback set by `set_plugin_icon_resolver()`. Supports `.png`/`.svg`/`.ico` extensions. Font size priority: per-button `label_size` > 0 → use that value; otherwise → `AppSettings.default_label_size`. Buttons are right-click editable via `ButtonEditorDialog` (uses `QStackedWidget` per action type, plus dynamically added plugin editor widgets; includes `HotkeyRecorderWidget` for keyboard capture with `grabKeyboard()`, color picker for label color, font size spin box); Launch App page has "Browse..." (file picker) and "Find App..." (`AppFinderDialog` — two-tab dialog scanning running processes via psutil and Start Menu .lnk shortcuts via WScript.Shell COM, displays exe icons via `QFileIconProvider`, saves selected icon as PNG to `%APPDATA%/SoftDeck/icons/` and auto-fills Path + Working Dir + Icon fields). Button context menu also supports Copy/Paste to duplicate button configs across positions. **Button drag-and-drop swap:** `DeckButton` supports left-click drag to swap positions with another button. Uses custom MIME type `application/x-deckbutton-pos` carrying `(row,col)`. Drag threshold is `QApplication.startDragDistance()`; empty buttons cannot be dragged but can receive drops. Drop on occupied cell swaps both `ButtonConfig.position` values; drop on empty cell moves the source button. Visual feedback: accent border on drag-over target, semi-transparent `grab()` pixmap as drag image. All dialog `.exec()` calls are wrapped with `set_numpad_passthrough(True/False)` to allow numpad input while editing. Folders managed via `FolderEditorDialog` (includes "Find App..." button that opens `AppFinderDialog` to select running processes/Start Menu apps, adds exe filename to mapped apps list). Settings via `SettingsDialog` (button size/spacing/default font/default font size, behavior (auto-switch/always-on-top), appearance (theme selector/opacity) — grid rows/cols hidden from UI). `TrayIcon` provides show/settings/reset position/quit context menu and double-click to show. **Toast notifications** (`toast.py`): custom themed `_ToastWidget` (frameless `ToolTip` window with `WA_TranslucentBackground` + `WA_ShowWithoutActivating`) managed by `ToastManager`. Each toast has a themed background (`bg_elevated`), accent-colored left bar (type-specific: INFO=theme accent, SUCCESS=green, WARNING=amber, ERROR=red), progress bar at bottom that shrinks over the duration. Animation: slide-up + fade-in (300ms OutCubic), auto-dismiss with fade-out (250ms InCubic). Click to dismiss early. Multiple toasts stack upward from bottom-right of primary screen (above taskbar). `ToastManager.set_palette()` syncs with theme changes via `MainWindow.apply_theme()`. **Window focus management:** `MainWindow.showEvent()` reinforces `WS_EX_NOACTIVATE` to prevent click-through focus stealing. `launch_with_foreground(callback)` temporarily claims foreground, executes the launch callback, then schedules a fallback timer (800ms) to bring the new app window to front via the `SetWindowPos` TOPMOST/NOTOPMOST trick. Version label (`v{APP_VERSION}`) shown bottom-right with minimal opacity.

5. **Styles** (`src/ui/styles.py`) — Multi-theme system with semantic color palettes. `ThemePalette` (frozen dataclass) defines ~25 semantic colors (background hierarchy, borders, text levels, accent, splash, etc.). `ThemeStylesheets` (frozen dataclass) holds pre-generated stylesheets for a palette. `get_theme(name)` resolves and caches a `ThemeStylesheets` instance. 10 built-in themes: `dark` (default), `light`, `solarized_light`, `midnight`, `emerald`, `violet`, `nord`, `dracula`, `amber`, `cyber`. Backward-compat module-level constants (`DARK_THEME`, `DECK_BUTTON_STYLE`, etc.) resolve to the `dark` theme. `MainWindow.apply_theme(name)` switches themes at runtime — updates QApplication global stylesheet, title bar, folder tree, version label, toast manager palette, and button styles.

6. **Native Hook** (`src/native/`) — C DLL (`numpad_hook.dll`) that implements `WH_KEYBOARD_LL` keyboard hook in a separate process for reliable key suppression.

   **Why a separate process?** Two constraints forced this architecture:
   - **PyInstaller exe cannot suppress keyboard hooks.** When `WH_KEYBOARD_LL` hook callback returns 1 (suppress) from a PyInstaller-bundled exe, Windows ignores the suppression — the hook fires and sees the key, but the key still reaches the target app (e.g. VSCode). The same code works perfectly from `python.exe` (signed/trusted). This appears to be a Windows security/trust issue with unsigned executables.
   - **Corporate security software deletes new `.exe` files** compiled with MinGW/gcc, but leaves `.dll` files alone.

   **Solution:** `rundll32.exe` (trusted Windows system binary) hosts the DLL. Python launches `rundll32.exe "path\numpad_hook.dll",start_entry <parent_pid>`. The DLL's `start_entry` function starts the hook thread, creates shared memory, and blocks until either Python sets `running=0` or the parent process (identified by PID) dies.

   **Architecture:**
   - `numpad_hook.dll` — hook callback (`hook_proc`) + shared memory IPC + `start_entry` for rundll32
   - `SharedData` struct (packed, matches Python `_SharedData` in `input_detector.py`): lock-free ring buffer (`ev_write`/`ev_read`/`events[256]`), Num Lock state (`nl_changed`/`nl_new_state`/`numlock_off`), control flags (`passthrough`/`running`), debug counters (`any_key_count`/`suppressed`/`numpad_seen`/`hook_ok`)
   - Shared memory name: `Local\SoftDeck_NumpadHook`
   - Hook suppresses numpad nav keys (scan 71–73, 75–77, 79–82) when `numlock_off=1` and `passthrough=0`, writing scan codes to the ring buffer
   - The hook thread uses `SetTimer` (200ms) to check the `running` flag and `PostQuitMessage` when it's 0
   - Compile: `gcc -shared -O2 -o numpad_hook.dll numpad_hook.c -luser32 -lkernel32` (requires MSYS2 MinGW64, `PATH` must include `/c/msys64/mingw64/bin:/c/msys64/usr/bin`)

7. **Plugins** (`src/plugins/`) — Auto-discovered plugin system for extending action types. `PluginBase` (ABC in `base.py`) defines the plugin interface: `get_action_type()`, `get_display_name()`, `create_action()` (required); `create_editor()`, `get_icon_path(params)`, `initialize()`, `shutdown()` (optional). `PluginEditorWidget` (ABC) defines custom editor UI: `create_widget(parent)`, `load_params(params)`, `get_params()`. `PluginLoader` (`loader.py`) scans `src/plugins/*/` sub-packages via `pkgutil.iter_modules()`, imports each, and looks for a `Plugin` class. Plugin actions are registered into `ActionRegistry` alongside built-in actions (indistinguishable at dispatch time). Plugin editors are dynamically added to `ButtonEditorDialog`'s `QStackedWidget`. Plugin icon paths fall through the icon resolver chain: per-button icon > built-in `ACTION_ICON_MAP` > plugin `get_icon_path()`. To add a new plugin: create `src/plugins/my_feature/` with `__init__.py` (exports `Plugin = MyFeaturePlugin`), `plugin.py` (subclasses `PluginBase`), `action.py` (subclasses `ActionBase`), optionally `editor.py` (subclasses `PluginEditorWidget`).

   **Current plugin — `media_control`** (`src/plugins/media_control/`):
   - `MediaControlPlugin` — registers action type `"media_control"`, provides `MediaControlAction` + `MediaControlEditorWidget` + `MediaControlService` + `MediaPlaybackMonitor`. Tracks `_is_playing` and `_is_muted` state flags for dynamic icon resolution. `get_service()` exposes the `MediaControlService` for mute polling.
   - `MediaControlAction` — 7 commands: `play_pause`/`next_track`/`prev_track`/`stop` (via `keyboard.send()` media keys), `volume_up`/`volume_down`/`mute` (via pycaw `IAudioEndpointVolume`)
   - `MediaControlService` — wraps pycaw `AudioUtilities.GetSpeakers().EndpointVolume` for volume get/set/mute. `is_muted()` returns current mute state (polled from main thread via `QTimer` in `SoftDeckApp`)
   - `MediaPlaybackMonitor(QThread)` — polls Windows SMTC (System Media Transport Controls) via WinRT `GlobalSystemMediaTransportControlsSessionManager` every 1s, emits `playback_state_changed(bool)`. Gracefully degrades if WinRT unavailable (`available=False`). Used for dynamic play/pause button icon (shows play or pause icon based on playback state)
   - `MediaControlEditorWidget` — `QComboBox` command selector + per-state toggle settings. `_TOGGLE_COMMANDS` dict defines which commands (`play_pause`, `mute`) get per-state icon/label UI groups. For `play_pause`: Play Icon/Label + Pause Icon/Label; for `mute`: Mute Icon/Label + Unmute Icon/Label. Groups show/hide based on selected command. Param keys: `play_icon`/`play_label`/`pause_icon`/`pause_label` (play_pause), `mute_icon`/`mute_label`/`unmute_icon`/`unmute_label` (mute). Empty values are omitted from saved params.
   - Icons at `assets/icons/actions/media_control/`, dynamic: `play_pause` resolves to `play.svg` or `pause.svg` based on `_is_playing` flag; `mute` resolves to `muted.{ext}` or `unmuted.{ext}` based on `_is_muted` flag (falls back to static `mute.{ext}` if state-specific files missing)
   - **Mute state polling:** `SoftDeckApp` creates a `QTimer` (500ms) that polls `MediaControlService.is_muted()` in the main thread (avoids COM threading issues with pycaw). On state change: updates `plugin._is_muted` + calls `MainWindow.update_mute_state()`. `MainWindow` caches `_last_media_muted` and re-applies to buttons on folder reload, mirroring the existing `_last_media_playing` pattern.

**Key data flow:** Config defines a root folder tree → each folder has `buttons` and `children` (sub-folders) → the grid shows the current folder's buttons → each button has an `ActionConfig(type, params)` → on click, `ActionRegistry.execute(type, params)` dispatches to the matching `ActionBase` subclass (built-in or plugin-provided) → services feed live data back to the UI via Qt signals. The folder tree panel allows navigation between folders; clicking a folder loads its buttons into the grid. Buttons can be copied/pasted via `DeckButton._clipboard` (class-level dict storing `ButtonConfig.to_dict()` data) or rearranged via drag-and-drop swap; `ActionConfig.params` uses `copy.deepcopy` in `to_dict()`/`from_dict()` to ensure pasted buttons are fully independent from originals.

**Keyboard shortcuts:** Global numpad keys (Num Lock OFF, via `InputDetector` hook) map numpad-layout keys (7-8-9/4-5-6/1-2-3) to grid positions `(row, col)` in the top-left 3x3 area. Numpad 0 navigates back to the parent folder (no-op at root).

**Window behavior:** `closeEvent` minimizes to tray instead of quitting. `toggle_visibility` hides to tray or `show_on_primary()` (restores to last saved position, or centers on primary screen top edge if none saved). Window position is persisted to `AppSettings.window_x`/`window_y` on every move via `moveEvent`. `reset_position()` clears saved position and centers on primary screen (accessible via tray menu "Reset Position"). Window uses `setMinimumSize` (not `setFixedSize`) to allow drag resize. `set_opacity(value)` applies opacity and persists to config. TitleBar has a horizontal `QSlider` (20–100%) for real-time opacity control. **Num Lock–driven visibility:** Num Lock ON hides the window, Num Lock OFF shows it. This is checked both at startup and on every Num Lock toggle via `InputDetector`. On Num Lock OFF, `_on_numlock_changed` re-verifies actual Num Lock state via `is_numlock_on()` before showing, then calls `_sync_folder_to_foreground()` to immediately check the current foreground app and switch to its mapped folder (bypasses `ActiveWindowMonitor`'s change-only detection).

**Folder tree drag-and-drop:** `FolderTreeWidget.dropEvent` handles moves entirely through `ConfigManager.move_folder()` + `rebuild()`. The event is accepted with `IgnoreAction` drop action to prevent Qt's `InternalMove` mode from deleting the source row after our rebuild.

## Windows API Usage

The app relies heavily on Windows-specific APIs:

- **ctypes.windll.kernel32** — `CreateMutexW`/`GetLastError`/`CloseHandle` (single-instance mutex in `main.py` + `app.py`), `OpenFileMappingW`/`MapViewOfFile`/`UnmapViewOfFile` (shared memory IPC in `input_detector.py`), `GetCurrentThreadId`/`AttachThreadInput` (foreground window manipulation in `main_window.py`)
- **ctypes.windll.user32** — `GetKeyState(VK_NUMLOCK)` (Num Lock detection in `input_detector.py`), `SetWindowPos`/`SetForegroundWindow`/`GetForegroundWindow`/`EnumWindows`/`GetWindowLongW`/`SetWindowLongW`/`IsWindowVisible`/`GetWindowThreadProcessId` (window management in `main_window.py`), `LockWorkStation` (Win+L special hotkey in `hotkey.py`)
- **pywin32** — `win32gui.GetForegroundWindow`/`win32process.GetWindowThreadProcessId` (foreground app detection in `app.py` + `window_monitor.py`), `win32clipboard` (clipboard paste mode in `text_input.py` + `macro.py`), `win32com.client.Dispatch("WScript.Shell")` (Start Menu .lnk shortcut parsing in `app_finder_dialog.py`)
- **pycaw** — `AudioUtilities.GetSpeakers().EndpointVolume` (volume get/set/mute in `plugins/media_control/service.py`)
- **WinRT** — `winrt.windows.media.control.GlobalSystemMediaTransportControlsSessionManager` (SMTC playback state detection in `plugins/media_control/playback_monitor.py`; optional — gracefully degrades if unavailable)
- **keyboard** — `keyboard.send()` (hotkeys + media keys), `keyboard.write()` (text input); monkey-patched in `app.py` to prevent `WH_KEYBOARD_LL` hook installation (`_kb._listener.start_if_necessary = lambda: None`)
- **Native DLL** — `numpad_hook.dll` loaded via `rundll32.exe`: `SetWindowsHookExW(WH_KEYBOARD_LL)`, `CreateFileMappingW` (shared memory), `SetTimer`/`PostQuitMessage` (lifecycle), `InterlockedIncrement`/`InterlockedExchange` (lock-free ring buffer)
- **Other** — `os.startfile()` (app/URL launching), `subprocess.Popen` with `CREATE_NEW_CONSOLE`/`CREATE_NO_WINDOW` flags, `winsound.PlaySound` (ready sound), `psutil` (process enumeration + CPU/RAM stats)

## Conventions

- All modules use `from __future__ import annotations` and `TYPE_CHECKING` guards for type-only imports
- Private attributes prefixed with `_`; no public setters except through property accessors
- Qt signals/slots for all cross-component communication
- Button positions are `(row, col)` tuples
- Config uses `to_dict()`/`from_dict()` pattern (no Pydantic)
- Dialogs use lazy imports to avoid circular dependencies
- Services are injected via setter methods (e.g., `set_main_window()`, `set_media_service()`, `set_input_detector()`, `set_toast_manager()`)
- New folder IDs use `uuid.uuid4().hex[:8]`
- Config version is 2; v1 configs are auto-migrated on load
- App version tracked in `src/version.py` (`APP_VERSION`), persisted in config for migration detection
- Plugins export `Plugin = MyPlugin` in `__init__.py`; loader discovers via `pkgutil.iter_modules()`

## File Map

```
main.py                          # Entry point — Win32 Named Mutex single-instance check before any imports
src/version.py                   # APP_VERSION constant ("0.1.0-beta")
src/app.py                       # SoftDeckApp — orchestrates everything (keyboard listener monkey-patched to prevent hook conflicts)
src/config/models.py             # Dataclasses: AppConfig, AppSettings, FolderConfig, ButtonConfig, ActionConfig (+ deprecated PageConfig for migration)
src/config/manager.py            # ConfigManager — load/save with atomic writes + folder CRUD + export/import
src/actions/base.py              # ActionBase ABC
src/actions/registry.py          # ActionRegistry — type→action dispatch + main_window ref
src/actions/launch_app.py        # LaunchAppAction — launch_with_foreground wrapper / subprocess.Popen(CREATE_NEW_CONSOLE) with args
src/actions/hotkey.py            # HotkeyAction — keyboard.send() + _SPECIAL_HOTKEYS (win+l → LockWorkStation, lazily initialized)
src/actions/text_input.py        # TextInputAction — keyboard.write() or clipboard paste (win32clipboard + Ctrl+V) via use_clipboard param
src/actions/navigate.py          # NavigateFolderAction — folder switching via registry.main_window
src/actions/system_monitor.py    # SystemMonitorAction — display-only, live data via DeckButton
src/actions/open_url.py          # OpenUrlAction — os.startfile() (Windows shell default browser)
src/actions/macro.py             # MacroAction — sequential execution of hotkey/text/delay steps
src/actions/run_command.py       # RunCommandAction — shell command execution via subprocess
src/plugins/base.py              # PluginBase ABC + PluginEditorWidget ABC
src/plugins/loader.py            # PluginLoader — auto-discovery via pkgutil, lifecycle management, editor/icon delegation
src/plugins/media_control/       # Media Control plugin:
  __init__.py                    #   Exports Plugin = MediaControlPlugin
  plugin.py                      #   MediaControlPlugin — factory + lifecycle + dynamic icon resolution
  action.py                      #   MediaControlAction — 7 commands (media keys via keyboard, volume via pycaw)
  editor.py                      #   MediaControlEditorWidget — QComboBox command selector + per-state toggle icon/label editor (play_pause, mute)
  service.py                     #   MediaControlService — pycaw IAudioEndpointVolume wrapper
  playback_monitor.py            #   MediaPlaybackMonitor(QThread) — WinRT SMTC polling for play/pause state
src/services/system_stats.py     # SystemStatsService(QThread) — CPU/RAM polling
src/services/window_monitor.py   # ActiveWindowMonitor(QThread) — foreground window tracking
src/services/input_detector.py   # InputDetector — launches rundll32+numpad_hook.dll, polls shared memory via QTimer (16ms)
src/native/numpad_hook.c         # C DLL source — WH_KEYBOARD_LL hook + shared memory IPC + rundll32 entry point
src/native/numpad_hook.dll       # Compiled DLL (bundled into exe via PyInstaller --add-binary)
src/native/numpad_hook_console.c # Console debug version of the hook (standalone, not used in production)
src/ui/main_window.py           # MainWindow + TitleBar — frameless resizable window, QSplitter(tree|grid), opacity slider, position persistence, launch_with_foreground, apply_theme, update_media_state/update_mute_state propagation
src/ui/button_widget.py         # DeckButton(QPushButton) — themed buttons, custom paintEvent (icon behind text, default icon fallback), context menu (edit/clear/copy/paste), drag-and-drop swap, per-state media toggle updates (_MEDIA_TOGGLE_KEYS)
src/ui/default_icons.py         # Action type → default icon path resolver (ACTION_ICON_MAP + plugin fallback via _plugin_icon_resolver)
src/ui/toast.py                 # ToastManager + _ToastWidget — themed toast notifications (slide-up, fade, progress bar, stacking)
src/ui/app_finder_dialog.py     # AppFinderDialog — find apps via running processes (psutil) or Start Menu (.lnk), shows exe icons, saves selected icon as PNG
src/ui/folder_tree.py           # FolderTreeWidget(QTreeWidget) — left panel folder tree with drag-and-drop
src/ui/folder_editor_dialog.py  # FolderEditorDialog — name + mapped apps list for folders + "Find App..." button (reuses AppFinderDialog)
src/ui/button_editor_dialog.py  # ButtonEditorDialog — per-action-type stacked editor + plugin editors + HotkeyRecorderWidget + Find App button for launch_app
src/ui/settings_dialog.py       # SettingsDialog — grid/behavior/appearance settings + theme selector
src/ui/styles.py                # ThemePalette + ThemeStylesheets + 10 built-in themes + get_theme() resolver
src/ui/tray_icon.py             # TrayIcon(QSystemTrayIcon) — system tray with context menu (show/settings/reset position/quit)
assets/icons/actions/            # Default action icons: {type}.png per action, media_control/{command}.png for media sub-commands
config/default_config.json       # Default grid: Root(media+monitor) → Apps(system utils) → Shortcuts(hotkeys) (v2 format)
USAGE.md                         # User manual — reference (Korean)
GUIDE.md                         # User manual — beginner-friendly guide (Korean)
docs/build_pdf.py                # Script to regenerate the PDF guide
```
