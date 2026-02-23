from __future__ import annotations

import logging

import psutil
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class SystemStatsService(QThread):
    stats_updated = pyqtSignal(float, float)  # cpu_percent, ram_percent

    def __init__(self, interval_ms: int = 2000) -> None:
        super().__init__()
        self._interval_ms = interval_ms
        self._running = True

    def run(self) -> None:
        # First call to initialize cpu_percent
        psutil.cpu_percent(interval=None)

        while self._running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                self.stats_updated.emit(cpu, ram)
            except Exception:
                logger.exception("Failed to collect system stats")

            self.msleep(self._interval_ms)

    def stop(self) -> None:
        self._running = False
        self.quit()
        self.wait(3000)
