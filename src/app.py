from __future__ import annotations

import ctypes
import logging
import os
import sys
import time

import psutil

# Prevent the keyboard library from ever installing a WH_KEYBOARD_LL hook.
# Its hook interferes with our numpad_hook.exe even in a separate process.
import keyboard as _kb
_kb._listener.start_if_necessary = lambda: None

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .config.manager import ConfigManager
from .actions.registry import ActionRegistry
from .actions.launch_app import LaunchAppAction
from .actions.hotkey import HotkeyAction
from .actions.system_monitor import SystemMonitorAction
from .actions.navigate import NavigateFolderAction
from .actions.text_input import TextInputAction
from .actions.macro import MacroAction
from .actions.open_url import OpenUrlAction
from .actions.run_command import RunCommandAction
from .services.system_stats import SystemStatsService
from .services.window_monitor import ActiveWindowMonitor

from .services.input_detector import InputDetector
from .ui.main_window import MainWindow
from .ui.tray_icon import TrayIcon
from .ui.styles import get_theme
from .ui.toast import ToastManager
from .plugins.loader import PluginLoader

logger = logging.getLogger(__name__)

_MUTEX_NAME = "SoftDeck_SingleInstance"


class SoftDeckApp(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationName("SoftDeck")
        self.setQuitOnLastWindowClosed(False)

        self._instance_mutex = None
        self._setup_logging()

        # Single instance: kill existing process if running
        self._ensure_single_instance()

        # Config
        self._config_manager = ConfigManager()
        self._config_manager.load()

        # Resolve theme
        self._theme = get_theme(self._config_manager.settings.theme)

        # Toast notifications
        self._toast_manager = ToastManager(self._theme.palette)

        # Actions
        self._action_registry = ActionRegistry()
        self._register_actions()

        # Plugins
        self._plugin_loader = PluginLoader()
        self._load_plugins()

        # Input detector (injected key filter + global numpad shortcuts)
        self._input_detector = InputDetector()
        self._input_detector.start()

        # Main window
        self._main_window = MainWindow(self._config_manager, self._action_registry, self._plugin_loader)
        self._main_window.set_input_detector(self._input_detector)
        self._input_detector.numpad_signal.pressed.connect(self._main_window.on_global_numpad)
        self._input_detector.numpad_signal.back_pressed.connect(self._main_window.navigate_back)
        self._input_detector.numpad_signal.numlock_changed.connect(self._on_numlock_changed)
        self._action_registry.set_main_window(self._main_window)
        self._main_window.set_toast_manager(self._toast_manager)

        # Tray
        self._tray_icon = TrayIcon(self._main_window)
        self._tray_icon.show()

        # Services
        self._start_services()

        # Apply theme
        self.setStyleSheet(self._theme.dark_theme)

        # Show window only if Num Lock is OFF
        if self._input_detector.is_numlock_on():
            logger.info("Num Lock is ON at startup — window hidden")
        else:
            self._main_window.show()

        # Ready feedback
        self._notify_ready()

    def _setup_logging(self) -> None:
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        handlers: list[logging.Handler] = []

        # File log — always works, even in --windowed exe (no stdout)
        log_dir = os.path.join(
            os.environ.get("APPDATA", "."), "SoftDeck"
        )
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "app.log"), encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

        # Console log — only when stdout exists (not --windowed exe)
        if sys.stdout is not None:
            handlers.append(logging.StreamHandler(sys.stdout))

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=handlers,
        )

    def _register_actions(self) -> None:
        self._action_registry.register("launch_app", LaunchAppAction())
        self._action_registry.register("hotkey", HotkeyAction())
        self._action_registry.register("text_input", TextInputAction())
        self._action_registry.register("macro", MacroAction())
        self._action_registry.register("system_monitor", SystemMonitorAction())
        self._action_registry.register("open_url", OpenUrlAction())
        self._action_registry.register("run_command", RunCommandAction())

        nav_action = NavigateFolderAction(self._action_registry)
        self._action_registry.register("navigate_folder", nav_action)
        # Backward compat: old configs with navigate_page type
        self._action_registry.register("navigate_page", nav_action)

    def _load_plugins(self) -> None:
        self._plugin_loader.discover_and_load()
        for action_type, plugin in self._plugin_loader.plugins.items():
            self._action_registry.register(action_type, plugin.create_action())
        from .ui.default_icons import set_plugin_icon_resolver
        set_plugin_icon_resolver(self._plugin_loader.get_icon_path)

    def _start_services(self) -> None:
        # System stats
        self._stats_service = SystemStatsService(interval_ms=2000)
        self._stats_service.stats_updated.connect(self._main_window.update_monitor_button)
        self._main_window.set_system_stats_service(self._stats_service)
        self._stats_service.start()

        # Window monitor
        if self._config_manager.settings.auto_switch_enabled:
            self._window_monitor = ActiveWindowMonitor(interval_ms=300)
            self._window_monitor.active_app_changed.connect(self._on_active_app_changed)
            self._main_window.set_window_monitor(self._window_monitor)
            self._window_monitor.start()
        else:
            self._window_monitor = None

        # Media playback monitor
        self._playback_monitor = None
        self._mute_timer = None
        media_plugin = self._plugin_loader.plugins.get("media_control")
        if media_plugin is not None:
            monitor = media_plugin.get_playback_monitor()
            if monitor is not None and monitor.available:
                monitor.playback_state_changed.connect(self._on_media_state_changed)
                monitor.start()
                self._playback_monitor = monitor
                logger.info("Media playback monitor started")
            # Mute state polling (main-thread QTimer to avoid COM threading issues)
            service = media_plugin.get_service()
            if service is not None:
                self._last_mute_state = service.is_muted()
                self._mute_service = service
                self._mute_timer = QTimer()
                self._mute_timer.timeout.connect(self._poll_mute_state)
                self._mute_timer.start(500)
                logger.info("Mute state polling started")

    def _on_numlock_changed(self, is_on: bool) -> None:
        """Hide window when Num Lock is ON, show when OFF."""
        if is_on:
            self._main_window.hide()
        else:
            # Re-check actual Num Lock state before showing
            if self._input_detector.is_numlock_on():
                return
            self._main_window.show_on_primary()
            self._sync_folder_to_foreground()

    def _sync_folder_to_foreground(self) -> None:
        """Switch to the mapped folder for the current foreground app."""
        if not self._config_manager.settings.auto_switch_enabled:
            return
        if self._window_monitor is None:
            return
        try:
            import win32gui
            import win32process

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid or pid == os.getpid():
                return
            proc = psutil.Process(pid)
            exe_name = proc.name()
            folder = self._config_manager.find_folder_for_app(exe_name)
            if folder is not None:
                self._main_window.switch_to_folder_id(folder.id)
            # Keep the monitor in sync to avoid duplicate signal
            self._window_monitor._last_exe = exe_name
        except Exception:
            logger.debug("Failed to sync folder to foreground", exc_info=True)

    def _on_active_app_changed(self, exe_name: str) -> None:
        if not self._config_manager.settings.auto_switch_enabled:
            return
        folder = self._config_manager.find_folder_for_app(exe_name)
        if folder is not None:
            self._main_window.switch_to_folder_id(folder.id)

    def _on_media_state_changed(self, is_playing: bool) -> None:
        media_plugin = self._plugin_loader.plugins.get("media_control")
        if media_plugin is not None:
            media_plugin._is_playing = is_playing
        self._main_window.update_media_state(is_playing)

    def _poll_mute_state(self) -> None:
        try:
            muted = self._mute_service.is_muted()
        except Exception:
            return
        if muted != self._last_mute_state:
            self._last_mute_state = muted
            media_plugin = self._plugin_loader.plugins.get("media_control")
            if media_plugin is not None:
                media_plugin._is_muted = muted
            self._main_window.update_mute_state(muted)

    def _notify_ready(self) -> None:
        """Toast notification + system sound to signal app is ready."""
        import winsound
        self._toast_manager.show("SoftDeck", "Ready", duration_ms=2000)
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)

    # ------------------------------------------------------------------
    # Single-instance helpers
    # ------------------------------------------------------------------

    def _acquire_mutex(self) -> bool:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(handle)
            return False
        self._instance_mutex = handle
        return True

    def _kill_existing(self) -> None:
        my_pid = os.getpid()
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.pid == my_pid:
                    continue
                name = proc.info["name"] or ""
                if name.lower() == "softdeck.exe":
                    proc.terminate()
                    proc.wait(timeout=3)
                    logger.info("Terminated existing PID %d", proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    logger.info("Force-killed existing PID %d", proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    def _ensure_single_instance(self) -> None:
        if self._acquire_mutex():
            return

        logger.info("Another instance detected — terminating it")
        self._kill_existing()

        for _ in range(20):
            time.sleep(0.25)
            self.processEvents()
            if self._acquire_mutex():
                logger.info("Mutex acquired after killing existing process")
                return

        logger.error("Failed to acquire mutex after killing existing process")
        sys.exit(1)

    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        logger.info("Shutting down...")
        if hasattr(self, "_tray_icon"):
            self._tray_icon.hide()
        if hasattr(self, "_input_detector"):
            self._input_detector.stop()
        if hasattr(self, "_stats_service"):
            self._stats_service.stop()
        if hasattr(self, "_window_monitor") and self._window_monitor is not None:
            self._window_monitor.stop()
        if hasattr(self, "_playback_monitor") and self._playback_monitor is not None:
            self._playback_monitor.stop()
        if hasattr(self, "_plugin_loader"):
            self._plugin_loader.shutdown_all()
        if self._instance_mutex:
            ctypes.windll.kernel32.CloseHandle(self._instance_mutex)
            self._instance_mutex = None
