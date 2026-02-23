from __future__ import annotations

import logging
import os

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

_OWN_PID = os.getpid()


class ActiveWindowMonitor(QThread):
    active_app_changed = pyqtSignal(str)  # exe_name

    def __init__(self, interval_ms: int = 300) -> None:
        super().__init__()
        self._interval_ms = interval_ms
        self._running = True
        self._last_exe = ""

    def run(self) -> None:
        import win32gui
        import win32process
        import psutil as _psutil

        while self._running:
            try:
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid and pid != _OWN_PID:
                        try:
                            proc = _psutil.Process(pid)
                            exe_name = proc.name()
                            if exe_name != self._last_exe:
                                self._last_exe = exe_name
                                self.active_app_changed.emit(exe_name)
                        except (_psutil.NoSuchProcess, _psutil.AccessDenied):
                            pass
            except Exception:
                pass  # Window may have closed between check and query

            self.msleep(self._interval_ms)

    def stop(self) -> None:
        self._running = False
        self.quit()
        self.wait(3000)
