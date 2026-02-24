from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSharedMemory

from .config.manager import ConfigManager
from .actions.registry import ActionRegistry
from .actions.launch_app import LaunchAppAction
from .actions.hotkey import HotkeyAction
from .actions.media import MediaControlAction
from .actions.system_monitor import SystemMonitorAction
from .actions.navigate import NavigateFolderAction
from .actions.text_input import TextInputAction
from .actions.macro import MacroAction
from .services.media_control import MediaControlService
from .services.system_stats import SystemStatsService
from .services.window_monitor import ActiveWindowMonitor
from .services.global_hotkey import GlobalHotkeyService
from .services.input_detector import InputDetector
from .ui.main_window import MainWindow
from .ui.tray_icon import TrayIcon
from .ui.styles import DARK_THEME

logger = logging.getLogger(__name__)


class SteamDeckSoftApp(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationName("SteamDeckSoft")
        self.setQuitOnLastWindowClosed(False)

        # Single instance check
        self._shared_memory = QSharedMemory("SteamDeckSoft_SingleInstance")
        if self._shared_memory.attach():
            logger.warning("Another instance is already running.")
            self._already_running = True
            return
        self._shared_memory.create(1)
        self._already_running = False

        self._setup_logging()

        # Config
        self._config_manager = ConfigManager()
        self._config_manager.load()

        # Actions
        self._action_registry = ActionRegistry()
        self._register_actions()

        # Input detector (injected key filter + global numpad shortcuts)
        self._input_detector = InputDetector()
        self._input_detector.start()

        # Main window
        self._main_window = MainWindow(self._config_manager, self._action_registry)
        self._main_window.set_input_detector(self._input_detector)
        self._input_detector.numpad_signal.pressed.connect(self._main_window.on_global_numpad)
        self._input_detector.numpad_signal.numlock_changed.connect(self._on_numlock_changed)
        self._action_registry.set_main_window(self._main_window)

        # Tray
        self._tray_icon = TrayIcon(self._main_window)
        self._tray_icon.show()

        # Services
        self._start_services()

        # Global hotkey
        self._global_hotkey = GlobalHotkeyService(
            self._config_manager.settings.global_hotkey
        )
        self._global_hotkey.triggered.connect(self._main_window.toggle_visibility)
        self._global_hotkey.start()

        # Apply theme
        self.setStyleSheet(DARK_THEME)

        # Show window only if Num Lock is OFF
        if self._input_detector.is_numlock_on():
            logger.info("Num Lock is ON at startup — window hidden")
        else:
            self._main_window.show()

    @property
    def already_running(self) -> bool:
        return self._already_running

    def _setup_logging(self) -> None:
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    def _register_actions(self) -> None:
        # Media service
        self._media_service = MediaControlService()

        # Register actions
        self._action_registry.register("launch_app", LaunchAppAction())
        self._action_registry.register("hotkey", HotkeyAction())
        self._action_registry.register("text_input", TextInputAction())
        self._action_registry.register("macro", MacroAction())

        media_action = MediaControlAction()
        media_action.set_media_service(self._media_service)
        self._action_registry.register("media_control", media_action)

        self._action_registry.register("system_monitor", SystemMonitorAction())

        nav_action = NavigateFolderAction(self._action_registry)
        self._action_registry.register("navigate_folder", nav_action)
        # Backward compat: old configs with navigate_page type
        self._action_registry.register("navigate_page", nav_action)

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

    def _on_numlock_changed(self, is_on: bool) -> None:
        """Hide window when Num Lock is ON, show when OFF."""
        if is_on:
            self._main_window.hide()
        else:
            self._main_window.show_on_primary()

    def _on_active_app_changed(self, exe_name: str) -> None:
        if not self._config_manager.settings.auto_switch_enabled:
            return
        folder = self._config_manager.find_folder_for_app(exe_name)
        if folder is not None:
            self._main_window.switch_to_folder_id(folder.id)

    def cleanup(self) -> None:
        logger.info("Shutting down...")
        if hasattr(self, "_global_hotkey"):
            self._global_hotkey.stop()
        if hasattr(self, "_input_detector"):
            self._input_detector.stop()
        if hasattr(self, "_stats_service"):
            self._stats_service.stop()
        if hasattr(self, "_window_monitor") and self._window_monitor is not None:
            self._window_monitor.stop()
