from __future__ import annotations

import logging
from typing import Any

from .base import ActionBase

logger = logging.getLogger(__name__)


class NavigatePageAction(ActionBase):
    def __init__(self, registry) -> None:
        self._registry = registry

    def execute(self, params: dict[str, Any]) -> None:
        page_id = params.get("page_id", "")
        if not page_id:
            logger.warning("navigate_page: no page_id specified")
            return
        window = self._registry.main_window
        if window is not None:
            window.switch_to_page_id(page_id)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
