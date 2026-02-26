from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QFont, QIcon, QMouseEvent, QPainter, QPixmap, QColor
from PyQt6.QtWidgets import QPushButton, QMenu, QStyleOptionButton, QStyle

from ..config.models import ButtonConfig

if TYPE_CHECKING:
    from ..actions.registry import ActionRegistry
    from .main_window import MainWindow

logger = logging.getLogger(__name__)



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
        self._icon_pixmap: QPixmap | None = None

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
        theme = self._main_window._theme
        if self._config is None or not self._config.action.type:
            self.setStyleSheet(theme.deck_button_empty_style)
            return

        if self._config.action.type == "system_monitor":
            style = theme.monitor_button_style
        else:
            style = theme.deck_button_style

        overrides: list[str] = []
        if self._config.label_color:
            overrides.append(f"color: {self._config.label_color};")
        if self._config.label_size:
            overrides.append(f"font-size: {self._config.label_size}px;")
        else:
            default_size = self._main_window._config_manager.settings.default_label_size
            if default_size != 10:
                overrides.append(f"font-size: {default_size}px;")
        default_family = self._main_window._config_manager.settings.default_label_family
        if default_family:
            overrides.append(f"font-family: '{default_family}';")
        if overrides:
            style += "\nQPushButton#deckButton { " + " ".join(overrides) + " }"
        self.setStyleSheet(style)

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

        # Load icon pixmap for custom painting (drawn behind text)
        if self._config.icon and os.path.isfile(self._config.icon):
            self._icon_pixmap = QPixmap(self._config.icon)
        else:
            self._icon_pixmap = None

    def paintEvent(self, event) -> None:
        if not (self._icon_pixmap and not self._icon_pixmap.isNull()):
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1) Draw button background (no text/icon)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ""
        opt.icon = QIcon()
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, painter, self)

        # 2) Draw icon
        padding = 10
        available = min(self.width(), self.height()) - padding * 2
        scaled = self._icon_pixmap.scaled(
            available, available,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

        # 3) Draw label text on top
        text = self.text()
        if text:
            label_color = (
                self._config.label_color
                if self._config and self._config.label_color
                else self._main_window._theme.palette.text_bright
            )
            painter.setPen(QColor(label_color))
            font = self.font()
            default_family = self._main_window._config_manager.settings.default_label_family
            if default_family:
                font.setFamily(default_family)
            if self._config and self._config.label_size:
                font_size = self._config.label_size
            else:
                font_size = self._main_window._config_manager.settings.default_label_size
            font.setPixelSize(font_size)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

        painter.end()

    _FOREGROUND_ACTIONS = frozenset({"launch_app", "open_url", "run_command"})

    def _on_clicked(self) -> None:
        if not (self._config and self._config.action.type):
            return

        action_type = self._config.action.type
        params = self._config.action.params

        if action_type in self._FOREGROUND_ACTIONS:
            self._main_window.launch_with_foreground(
                lambda: self._action_registry.execute(action_type, params),
            )
        else:
            self._action_registry.execute(action_type, params)

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
        self._main_window.set_numpad_passthrough(True)
        result = dialog.exec()
        self._main_window.set_numpad_passthrough(False)
        if result:
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
