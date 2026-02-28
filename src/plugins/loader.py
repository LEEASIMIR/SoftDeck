from __future__ import annotations

import importlib
import logging
import os
import pkgutil
from typing import Any

from .base import PluginBase, PluginEditorWidget

logger = logging.getLogger(__name__)


class PluginLoader:
    """Discovers and manages plugins under src/plugins/*/."""

    def __init__(self) -> None:
        self.plugins: dict[str, PluginBase] = {}

    def discover_and_load(self) -> None:
        """Scan src/plugins/*/ for sub-packages exposing a Plugin class."""
        plugins_dir = os.path.dirname(os.path.abspath(__file__))
        for importer, name, is_pkg in pkgutil.iter_modules([plugins_dir]):
            if not is_pkg:
                continue
            try:
                module = importlib.import_module(f".{name}", package=__package__)
                plugin_cls = getattr(module, "Plugin", None)
                if plugin_cls is None:
                    continue
                plugin: PluginBase = plugin_cls()
                plugin.initialize()
                action_type = plugin.get_action_type()
                self.plugins[action_type] = plugin
                logger.info("Loaded plugin: %s (%s)", name, action_type)
            except Exception:
                logger.exception("Failed to load plugin: %s", name)

    def get_action_types(self) -> list[tuple[str, str]]:
        """Return (action_type, display_name) pairs for all loaded plugins."""
        return [
            (p.get_action_type(), p.get_display_name())
            for p in self.plugins.values()
        ]

    def get_editor(self, action_type: str) -> PluginEditorWidget | None:
        """Return the editor widget for an action type, or None."""
        plugin = self.plugins.get(action_type)
        if plugin is None:
            return None
        return plugin.create_editor()

    def get_icon_path(self, action_type: str, params: dict[str, Any]) -> str:
        """Delegate icon resolution to the plugin."""
        plugin = self.plugins.get(action_type)
        if plugin is None:
            return ""
        return plugin.get_icon_path(params)

    def shutdown_all(self) -> None:
        """Shut down all plugins."""
        for action_type, plugin in self.plugins.items():
            try:
                plugin.shutdown()
            except Exception:
                logger.exception("Error shutting down plugin: %s", action_type)
