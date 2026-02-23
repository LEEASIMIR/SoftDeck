from __future__ import annotations

import logging
from typing import Any

import keyboard

from .base import ActionBase

logger = logging.getLogger(__name__)


class HotkeyAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        keys = params.get("keys", "")
        if not keys:
            logger.warning("hotkey: no keys specified")
            return

        try:
            keyboard.send(keys)
            logger.info("Sent hotkey: %s", keys)
        except Exception:
            logger.exception("Failed to send hotkey: %s", keys)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
