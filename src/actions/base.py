from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ActionBase(ABC):
    @abstractmethod
    def execute(self, params: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_display_text(self, params: dict[str, Any]) -> str | None:
        """Return dynamic text for button display, or None to use label."""
        return None
