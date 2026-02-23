from __future__ import annotations

import logging

import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class GlobalHotkeyService(QObject):
    triggered = pyqtSignal()

    def __init__(self, hotkey: str = "ctrl+`", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._hotkey = hotkey
        self._registered = False

    def start(self) -> None:
        if self._registered:
            return
        try:
            keyboard.add_hotkey(self._hotkey, self._on_hotkey, suppress=True)
            self._registered = True
            logger.info("Global hotkey registered: %s", self._hotkey)
        except Exception:
            logger.exception("Failed to register global hotkey: %s", self._hotkey)

    def stop(self) -> None:
        if not self._registered:
            return
        try:
            keyboard.remove_hotkey(self._hotkey)
        except Exception:
            pass
        self._registered = False

    def update_hotkey(self, new_hotkey: str) -> None:
        self.stop()
        self._hotkey = new_hotkey
        self.start()

    def _on_hotkey(self) -> None:
        self.triggered.emit()
