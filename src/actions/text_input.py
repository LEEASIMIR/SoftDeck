from __future__ import annotations

import logging
from typing import Any

import keyboard

from .base import ActionBase

logger = logging.getLogger(__name__)


class TextInputAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        text = params.get("text", "")
        if not text:
            logger.warning("text_input: no text specified")
            return

        use_clipboard = params.get("use_clipboard", False)

        try:
            if use_clipboard:
                self._paste_via_clipboard(text)
            else:
                keyboard.write(text, delay=0.02)
            logger.info("Text input sent (%s): %s...",
                        "clipboard" if use_clipboard else "typing",
                        text[:30])
        except Exception:
            logger.exception("Failed to send text input")

    @staticmethod
    def _paste_via_clipboard(text: str) -> None:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()
        keyboard.send("ctrl+v")

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
