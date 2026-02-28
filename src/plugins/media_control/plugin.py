from __future__ import annotations

import os
import sys
from typing import Any

from ..base import PluginBase, PluginEditorWidget
from .action import MediaControlAction
from .service import MediaControlService
from .editor import MediaControlEditorWidget
from .playback_monitor import MediaPlaybackMonitor

# media_control command → sub-icon filename
_MEDIA_ICON_MAP: dict[str, str] = {
    "play_pause": "play_pause",
    "next_track": "next_track",
    "prev_track": "prev_track",
    "stop": "stop",
    "volume_up": "volume_up",
    "volume_down": "volume_down",
    "mute": "mute",
}


def _icons_dir() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(base, "assets", "icons", "actions", "media_control")


class MediaControlPlugin(PluginBase):
    def __init__(self) -> None:
        self._service: MediaControlService | None = None
        self._playback_monitor: MediaPlaybackMonitor | None = None
        self._is_playing: bool = False
        self._is_muted: bool = False

    def get_action_type(self) -> str:
        return "media_control"

    def get_display_name(self) -> str:
        return "Media Control"

    def initialize(self) -> None:
        self._service = MediaControlService()
        self._playback_monitor = MediaPlaybackMonitor()

    def get_playback_monitor(self) -> MediaPlaybackMonitor | None:
        return self._playback_monitor

    def get_service(self) -> MediaControlService | None:
        return self._service

    def create_action(self) -> MediaControlAction:
        action = MediaControlAction()
        if self._service is not None:
            action.set_media_service(self._service)
        return action

    def create_editor(self) -> PluginEditorWidget:
        return MediaControlEditorWidget()

    def get_icon_path(self, params: dict[str, Any]) -> str:
        command = params.get("command", "")
        icons = _icons_dir()

        # Dynamic toggle commands: try state-specific icon first
        if command == "play_pause":
            filename = "pause" if self._is_playing else "play"
            for ext in (".png", ".svg", ".ico"):
                path = os.path.join(icons, filename + ext)
                if os.path.isfile(path):
                    return path
            filename = "play_pause"  # static fallback
        elif command == "mute":
            filename = "unmuted" if self._is_muted else "muted"
            for ext in (".png", ".svg", ".ico"):
                path = os.path.join(icons, filename + ext)
                if os.path.isfile(path):
                    return path
            filename = "mute"  # static fallback
        else:
            filename = _MEDIA_ICON_MAP.get(command, "")

        if not filename:
            return ""
        for ext in (".png", ".svg", ".ico"):
            path = os.path.join(icons, filename + ext)
            if os.path.isfile(path):
                return path
        return ""

    def shutdown(self) -> None:
        if self._playback_monitor is not None:
            self._playback_monitor.stop()
            self._playback_monitor = None
        self._service = None
