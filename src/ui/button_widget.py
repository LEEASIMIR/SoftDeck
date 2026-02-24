from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QMouseEvent
from PyQt6.QtWidgets import QPushButton, QMenu

from ..config.models import ButtonConfig
from .styles import DECK_BUTTON_STYLE, DECK_BUTTON_EMPTY_STYLE, MONITOR_BUTTON_STYLE

if TYPE_CHECKING:
    from ..actions.registry import ActionRegistry
    from .main_window import MainWindow

logger = logging.getLogger(__name__)

_BUTTON_COLORS = [
    {"bg": "#16213e", "hover": "#1a2a50", "pressed": "#0f3460"},
    {"bg": "#1a1a3e", "hover": "#2a2050", "pressed": "#1a0f60"},
    {"bg": "#1e2a1e", "hover": "#2a3a2a", "pressed": "#1a3a1a"},
    {"bg": "#2a1a1a", "hover": "#3a2a2a", "pressed": "#3a1a1a"},
    {"bg": "#1a2a2a", "hover": "#2a3a3a", "pressed": "#1a3a3a"},
]


class DeckButton(QPushButton):
    _clipboard: dict | None = None  # class-level copied button data

    def __init__(
        self,
        row: int,
        col: int,
        config: ButtonConfig | None,
        action_registry: ActionRegistry,
        main_window: MainWindow,
        size: int = 100,
    ) -> None:
        super().__init__()
        self._row = row
        self._col = col
        self._config = config
        self._action_registry = action_registry
        self._main_window = main_window
        self._monitor_text: str | None = None

        self.setObjectName("deckButton")
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._apply_style()
        self._update_display()

        if self._config and self._config.action.type:
            self.clicked.connect(self._on_clicked)

    def _apply_style(self) -> None:
        if self._config is None or not self._config.action.type:
            self.setStyleSheet(DECK_BUTTON_EMPTY_STYLE)
            return

        if self._config.action.type == "system_monitor":
            self.setStyleSheet(MONITOR_BUTTON_STYLE)
            return

        color_index = (self._row * 5 + self._col) % len(_BUTTON_COLORS)
        colors = _BUTTON_COLORS[color_index]
        self.setStyleSheet(DECK_BUTTON_STYLE.format(**colors))

    def _update_display(self) -> None:
        if self._config is None:
            self.setText("")
            return

        # Check for dynamic display text
        if self._monitor_text is not None:
            self.setText(self._monitor_text)
            return

        display = self._action_registry.get_display_text(
            self._config.action.type, self._config.action.params
        )
        if display:
            self.setText(display)
        else:
            self.setText(self._config.label)

        # Set icon if available
        if self._config.icon and os.path.isfile(self._config.icon):
            self.setIcon(QIcon(self._config.icon))
            self.setIconSize(QSize(40, 40))

    def _on_clicked(self) -> None:
        if self._config and self._config.action.type:
            self._action_registry.execute(
                self._config.action.type,
                self._config.action.params,
            )

    def update_monitor_data(self, cpu: float, ram: float) -> None:
        if self._config and self._config.action.type == "system_monitor":
            self._monitor_text = f"CPU {cpu:.0f}%\nRAM {ram:.0f}%"
            self.setText(self._monitor_text)

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)

        edit_action = menu.addAction("Edit Button")
        clear_action = menu.addAction("Clear Button")
        menu.addSeparator()
        copy_action = menu.addAction("Copy Button")
        copy_action.setEnabled(self._config is not None and bool(self._config.action.type))
        paste_action = menu.addAction("Paste Button")
        paste_action.setEnabled(DeckButton._clipboard is not None)

        action = menu.exec(self.mapToGlobal(pos))

        if action == edit_action:
            self._edit_button()
        elif action == clear_action:
            self._clear_button()
        elif action == copy_action:
            self._copy_button()
        elif action == paste_action:
            self._paste_button()

    def _edit_button(self) -> None:
        from .button_editor_dialog import ButtonEditorDialog
        dialog = ButtonEditorDialog(
            self._config, self._row, self._col,
            self._main_window._config_manager, self._main_window
        )
        if dialog.exec():
            new_config = dialog.get_config()
            folder = self._main_window._config_manager.get_folder_by_id(
                self._main_window.get_current_folder_id()
            )
            if folder is not None:
                # Remove old config at this position
                folder.buttons = [b for b in folder.buttons if b.position != (self._row, self._col)]
                if new_config.action.type:
                    folder.buttons.append(new_config)
                self._main_window._config_manager.save()
                self._main_window._load_current_folder()
                # Update tree to reflect button count change
                if self._main_window._folder_tree is not None:
                    self._main_window._folder_tree.rebuild()

    def _clear_button(self) -> None:
        folder = self._main_window._config_manager.get_folder_by_id(
            self._main_window.get_current_folder_id()
        )
        if folder is not None:
            folder.buttons = [b for b in folder.buttons if b.position != (self._row, self._col)]
            self._main_window._config_manager.save()
            self._main_window._load_current_folder()
            if self._main_window._folder_tree is not None:
                self._main_window._folder_tree.rebuild()

    def _copy_button(self) -> None:
        if self._config is not None:
            DeckButton._clipboard = self._config.to_dict()

    def _paste_button(self) -> None:
        if DeckButton._clipboard is None:
            return
        new_config = ButtonConfig.from_dict(DeckButton._clipboard)
        new_config.position = (self._row, self._col)
        folder = self._main_window._config_manager.get_folder_by_id(
            self._main_window.get_current_folder_id()
        )
        if folder is not None:
            folder.buttons = [b for b in folder.buttons if b.position != (self._row, self._col)]
            folder.buttons.append(new_config)
            self._main_window._config_manager.save()
            self._main_window._load_current_folder()
            if self._main_window._folder_tree is not None:
                self._main_window._folder_tree.rebuild()

    def get_config(self) -> ButtonConfig | None:
        return self._config
