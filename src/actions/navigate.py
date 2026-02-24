from __future__ import annotations

import logging
from typing import Any

from .base import ActionBase

logger = logging.getLogger(__name__)


class NavigateFolderAction(ActionBase):
    def __init__(self, registry) -> None:
        self._registry = registry

    def execute(self, params: dict[str, Any]) -> None:
        folder_id = params.get("folder_id", "") or params.get("page_id", "")
        if not folder_id:
            logger.warning("navigate_folder: no folder_id specified")
            return
        window = self._registry.main_window
        if window is not None:
            window.switch_to_folder_id(folder_id)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
