from __future__ import annotations

import asyncio
import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# WinRT SMTC availability flag
_HAS_WINRT = False
try:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )
    _HAS_WINRT = True
except Exception:
    logger.debug("winrt not available — media playback monitoring disabled")


def _get_playback_status() -> bool | None:
    """Return True if playing, False if paused/stopped, None if unavailable."""
    if not _HAS_WINRT:
        return None
    try:
        loop = asyncio.new_event_loop()
        try:
            manager = loop.run_until_complete(
                SessionManager.request_async()
            )
            session = manager.get_current_session()
            if session is None:
                return False
            info = session.get_playback_info()
            return info.playback_status == PlaybackStatus.PLAYING
        finally:
            loop.close()
    except Exception:
        logger.debug("Failed to query playback status", exc_info=True)
        return None


class MediaPlaybackMonitor(QThread):
    """Polls Windows SMTC for media playback state changes."""

    playback_state_changed = pyqtSignal(bool)  # True = playing

    def __init__(self, interval_ms: int = 1000) -> None:
        super().__init__()
        self._interval_ms = interval_ms
        self._running = True
        self._last_state: bool | None = None

    @property
    def available(self) -> bool:
        return _HAS_WINRT

    def run(self) -> None:
        if not _HAS_WINRT:
            return

        while self._running:
            state = _get_playback_status()
            if state is not None and state != self._last_state:
                self._last_state = state
                self.playback_state_changed.emit(state)
            self.msleep(self._interval_ms)

    def stop(self) -> None:
        self._running = False
        self.quit()
        self.wait(3000)
