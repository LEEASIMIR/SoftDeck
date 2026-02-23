from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

if TYPE_CHECKING:
    from .main_window import MainWindow

logger = logging.getLogger(__name__)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, main_window: MainWindow) -> None:
        super().__init__(parent=main_window)
        self._main_window = main_window

        icon = QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        )
        self.setIcon(icon)
        self.setToolTip("SteamDeckSoft")

        menu = QMenu()

        show_action = QAction("Show", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self) -> None:
        self._main_window.show()
        self._main_window.activateWindow()

    def _open_settings(self) -> None:
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self._main_window._config_manager, self._main_window)
        if dialog.exec():
            self._main_window.reload_config()

    def _quit_app(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()
