from __future__ import annotations

import logging
import threading
import time
from typing import Any

import keyboard

from .base import ActionBase

logger = logging.getLogger(__name__)


class MacroAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        steps = params.get("steps", [])
        if not steps:
            logger.warning("macro: no steps defined")
            return

        threading.Thread(target=self._run_steps, args=(steps,), daemon=True).start()

    def _run_steps(self, steps: list[dict[str, Any]]) -> None:
        for i, step in enumerate(steps):
            step_type = step.get("type", "")
            step_params = step.get("params", {})
            try:
                if step_type == "hotkey":
                    keys = step_params.get("keys", "")
                    if keys:
                        keyboard.send(keys)
                        logger.info("Macro step %d: sent hotkey %s", i, keys)
                elif step_type == "text_input":
                    text = step_params.get("text", "")
                    if text:
                        if step_params.get("use_clipboard", False):
                            self._paste_via_clipboard(text)
                        else:
                            keyboard.write(text, delay=0.02)
                        logger.info("Macro step %d: text input (%d chars)", i, len(text))
                elif step_type == "delay":
                    ms = step_params.get("ms", 100)
                    time.sleep(ms / 1000)
                    logger.info("Macro step %d: delay %dms", i, ms)
                else:
                    logger.warning("Macro step %d: unknown type '%s'", i, step_type)
            except Exception:
                logger.exception("Macro step %d failed (type=%s)", i, step_type)

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
        steps = params.get("steps", [])
        if not steps:
            return None
        return f"Macro ({len(steps)} steps)"
