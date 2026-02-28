from __future__ import annotations

import logging
from typing import Any

import keyboard

from ...actions.base import ActionBase

logger = logging.getLogger(__name__)


class MediaControlAction(ActionBase):
    _MEDIA_KEYS = {
        "play_pause": "play/pause media",
        "next_track": "next track",
        "prev_track": "previous track",
        "stop": "stop media",
    }

    def __init__(self) -> None:
        self._media_service = None

    def set_media_service(self, service) -> None:
        self._media_service = service

    def execute(self, params: dict[str, Any]) -> None:
        command = params.get("command", "")
        if not command:
            logger.warning("media_control: no command specified")
            return

        try:
            if command == "volume_up":
                if self._media_service:
                    self._media_service.volume_up()
            elif command == "volume_down":
                if self._media_service:
                    self._media_service.volume_down()
            elif command == "mute":
                if self._media_service:
                    self._media_service.toggle_mute()
            elif command in self._MEDIA_KEYS:
                keyboard.send(self._MEDIA_KEYS[command])
            else:
                logger.warning("Unknown media command: %s", command)
                return
            logger.info("Media control: %s", command)
        except Exception:
            logger.exception("Failed media control: %s", command)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
