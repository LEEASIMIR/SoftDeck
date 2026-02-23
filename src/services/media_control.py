from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MediaControlService:
    def __init__(self) -> None:
        self._volume_interface = None
        self._init_audio()

    def _init_audio(self) -> None:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            logger.info("Audio endpoint initialized")
        except Exception:
            logger.exception("Failed to initialize audio endpoint")

    def get_volume(self) -> float:
        if self._volume_interface is None:
            return 0.0
        try:
            return self._volume_interface.GetMasterVolumeLevelScalar()
        except Exception:
            return 0.0

    def set_volume(self, level: float) -> None:
        if self._volume_interface is None:
            return
        try:
            level = max(0.0, min(1.0, level))
            self._volume_interface.SetMasterVolumeLevelScalar(level, None)
        except Exception:
            logger.exception("Failed to set volume")

    def volume_up(self, step: float = 0.05) -> None:
        current = self.get_volume()
        self.set_volume(current + step)

    def volume_down(self, step: float = 0.05) -> None:
        current = self.get_volume()
        self.set_volume(current - step)

    def toggle_mute(self) -> None:
        if self._volume_interface is None:
            return
        try:
            muted = self._volume_interface.GetMute()
            self._volume_interface.SetMute(not muted, None)
        except Exception:
            logger.exception("Failed to toggle mute")

    def is_muted(self) -> bool:
        if self._volume_interface is None:
            return False
        try:
            return bool(self._volume_interface.GetMute())
        except Exception:
            return False
