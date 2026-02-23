from __future__ import annotations

import logging
from typing import Any

from .base import ActionBase

logger = logging.getLogger(__name__)


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, ActionBase] = {}
        self._main_window = None

    def set_main_window(self, window) -> None:
        self._main_window = window

    @property
    def main_window(self):
        return self._main_window

    def register(self, action_type: str, action: ActionBase) -> None:
        self._actions[action_type] = action
        logger.debug("Registered action: %s", action_type)

    def execute(self, action_type: str, params: dict[str, Any]) -> None:
        action = self._actions.get(action_type)
        if action is None:
            logger.warning("Unknown action type: %s", action_type)
            return
        try:
            action.execute(params)
        except Exception:
            logger.exception("Action %s failed with params %s", action_type, params)

    def get_display_text(self, action_type: str, params: dict[str, Any]) -> str | None:
        action = self._actions.get(action_type)
        if action is None:
            return None
        try:
            return action.get_display_text(params)
        except Exception:
            return None

    def get_action(self, action_type: str) -> ActionBase | None:
        return self._actions.get(action_type)
