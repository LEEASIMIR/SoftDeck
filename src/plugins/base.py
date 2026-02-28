from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

    from ..actions.base import ActionBase


class PluginEditorWidget(ABC):
    """ABC for plugin-provided editor widgets in ButtonEditorDialog."""

    @abstractmethod
    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        """Create and return the editor QWidget."""
        ...

    @abstractmethod
    def load_params(self, params: dict[str, Any]) -> None:
        """Populate the editor from saved action params."""
        ...

    @abstractmethod
    def get_params(self) -> dict[str, Any]:
        """Return the current editor state as action params dict."""
        ...


class PluginBase(ABC):
    """ABC for SoftDeck plugins."""

    @abstractmethod
    def get_action_type(self) -> str:
        """Return the action type string (e.g. 'media_control')."""
        ...

    @abstractmethod
    def get_display_name(self) -> str:
        """Return the human-readable name (e.g. 'Media Control')."""
        ...

    @abstractmethod
    def create_action(self) -> ActionBase:
        """Create and return an ActionBase instance."""
        ...

    def create_editor(self) -> PluginEditorWidget | None:
        """Return a plugin editor widget, or None for no custom editor."""
        return None

    def get_icon_path(self, params: dict[str, Any]) -> str:
        """Return icon path for given params, or empty string."""
        return ""

    def initialize(self) -> None:
        """Called once after plugin discovery. Set up services here."""

    def shutdown(self) -> None:
        """Called on app exit. Clean up resources here."""
