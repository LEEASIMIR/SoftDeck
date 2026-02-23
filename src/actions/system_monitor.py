from __future__ import annotations

import logging
from typing import Any

from .base import ActionBase

logger = logging.getLogger(__name__)


class SystemMonitorAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        # Monitor buttons are display-only, no click action needed
        pass

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return "CPU ---%\nRAM ---%"
