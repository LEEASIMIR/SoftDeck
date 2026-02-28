from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QSize, QRect, QMimeData, QPoint
from PyQt6.QtGui import QFont, QIcon, QMouseEvent, QPainter, QPixmap, QColor, QDrag
from PyQt6.QtWidgets import QPushButton, QMenu, QStyleOptionButton, QStyle, QApplication

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
        self._scaled_icon: QPixmap | None = None
        self._scaled_icon_size: int = 0
        self._media_is_playing: bool = False
        self._media_is_muted: bool = False

        self._drag_start_pos: QPoint | None = None

        self.setObjectName("deckButton")
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._apply_style()
        self._update_display()

        if self._config and self._config.action.type:
            self.clicked.connect(self._on_clicked)

    def reconfigure(self, config: ButtonConfig | None, size: int) -> None:
        """Update this button with a new config without recreating the widget."""
        # Disconnect old clicked handler
        try:
            self.clicked.disconnect(self._on_clicked)
        except TypeError:
            pass

        self._config = config
        self._monitor_text = None
        self._icon_pixmap = None
        self._scaled_icon = None
        self._scaled_icon_size = 0

        self.setFixedSize(size, size)
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

    # Per-state param keys for media toggle commands
    # Maps command → ((active_icon_key, active_label_key), (inactive_icon_key, inactive_label_key))
    _MEDIA_TOGGLE_KEYS = {
        "play_pause": (("pause_icon", "pause_label"), ("play_icon", "play_label")),
        "mute": (("unmute_icon", "unmute_label"), ("mute_icon", "mute_label")),
    }

    def _get_media_toggle_state(self, command: str) -> bool:
        """Return True if in active state for the given toggle command."""
        if command == "play_pause":
            return self._media_is_playing
        if command == "mute":
            return self._media_is_muted
        return False

    def _update_display(self) -> None:
        if self._config is None:
            self.setText("")
            return

        # Check for dynamic display text
        if self._monitor_text is not None:
            self.setText(self._monitor_text)
            return

        params = self._config.action.params
        command = params.get("command", "") if self._config.action.type == "media_control" else ""
        toggle_keys = self._MEDIA_TOGGLE_KEYS.get(command)

        # Load icon pixmap for custom painting (drawn behind text)
        # Priority: per-state icon > custom icon > default action icon
        icon_path = ""
        has_state_label = False
        if toggle_keys:
            active = self._get_media_toggle_state(command)
            ico_key, lbl_key = toggle_keys[0] if active else toggle_keys[1]
            has_state_label = bool(params.get(lbl_key, ""))
            state_icon = params.get(ico_key, "")
            if state_icon and os.path.isfile(state_icon):
                icon_path = state_icon
        if not icon_path and self._config.icon and os.path.isfile(self._config.icon):
            icon_path = self._config.icon
        # Skip default icon if per-state label is set (text-only display)
        if not icon_path and self._config.action.type and not has_state_label:
            from .default_icons import get_default_icon_path
            icon_path = get_default_icon_path(self._config.action.type, params)

        if icon_path:
            self._icon_pixmap = QPixmap(icon_path)
        else:
            self._icon_pixmap = None
        self._scaled_icon = None
        self._scaled_icon_size = 0

        # Per-state label takes priority
        if toggle_keys:
            active = self._get_media_toggle_state(command)
            _, lbl_key = toggle_keys[0] if active else toggle_keys[1]
            state_label = params.get(lbl_key, "")
            if state_label:
                self.setText(state_label)
                return

        # If icon exists and label is empty, show icon only (no text)
        if self._icon_pixmap and not self._config.label:
            self.setText("")
            return

        display = self._action_registry.get_display_text(
            self._config.action.type, self._config.action.params
        )
        if display:
            self.setText(display)
        else:
            self.setText(self._config.label)

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

        # 2) Draw icon (cached scaled pixmap)
        padding = 10
        available = min(self.width(), self.height()) - padding * 2
        if self._scaled_icon is None or self._scaled_icon_size != available:
            self._scaled_icon = self._icon_pixmap.scaled(
                available, available,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._scaled_icon_size = available
        x = (self.width() - self._scaled_icon.width()) // 2
        y = (self.height() - self._scaled_icon.height()) // 2
        painter.drawPixmap(x, y, self._scaled_icon)

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

    # --- Drag and Drop ---

    _MIME_TYPE = "application/x-deckbutton-pos"

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if (
            event is None
            or self._drag_start_pos is None
            or not (event.buttons() & Qt.MouseButton.LeftButton)
        ):
            return
        if self._config is None or not self._config.action.type:
            return
        dist = (event.pos() - self._drag_start_pos).manhattanLength()
        if dist < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(self._MIME_TYPE, f"{self._row},{self._col}".encode())
        drag.setMimeData(mime)

        pixmap = self.grab()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 160))
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        self._drag_start_pos = None
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(self._MIME_TYPE):
            event.acceptProposedAction()
            self.setStyleSheet(
                self.styleSheet()
                + "\nQPushButton#deckButton { border: 2px solid #e94560; }"
            )

    def dragLeaveEvent(self, event) -> None:
        self._apply_style()

    def dropEvent(self, event) -> None:
        self._apply_style()
        data = event.mimeData().data(self._MIME_TYPE)
        if data.isEmpty():
            return
        try:
            src_row, src_col = (int(v) for v in bytes(data).decode().split(","))
        except (ValueError, IndexError):
            return

        dst_row, dst_col = self._row, self._col
        if (src_row, src_col) == (dst_row, dst_col):
            return

        folder = self._main_window._config_manager.get_folder_by_id(
            self._main_window.get_current_folder_id()
        )
        if folder is None:
            return

        src_cfg = next((b for b in folder.buttons if b.position == (src_row, src_col)), None)
        dst_cfg = next((b for b in folder.buttons if b.position == (dst_row, dst_col)), None)

        if src_cfg is None:
            return

        if dst_cfg is not None:
            src_cfg.position, dst_cfg.position = dst_cfg.position, src_cfg.position
        else:
            src_cfg.position = (dst_row, dst_col)

        self._main_window._config_manager.save()
        self._main_window._load_current_folder()

        event.acceptProposedAction()

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

    def _update_media_toggle(self, command: str) -> None:
        """Shared update for media toggle buttons (play_pause, mute)."""
        if not self._config or self._config.action.type != "media_control":
            return
        if self._config.action.params.get("command") != command:
            return

        params = self._config.action.params
        toggle_keys = self._MEDIA_TOGGLE_KEYS.get(command)
        if not toggle_keys:
            return

        active = self._get_media_toggle_state(command)
        ico_key, lbl_key = toggle_keys[0] if active else toggle_keys[1]

        # Resolve icon: per-state custom > button custom > default plugin icon
        icon_path = ""
        state_label = params.get(lbl_key, "")
        state_icon = params.get(ico_key, "")
        if state_icon and os.path.isfile(state_icon):
            icon_path = state_icon
        elif self._config.icon and os.path.isfile(self._config.icon):
            icon_path = self._config.icon
        elif not state_label:
            from .default_icons import get_default_icon_path
            icon_path = get_default_icon_path(self._config.action.type, params)

        if icon_path:
            self._icon_pixmap = QPixmap(icon_path)
        else:
            self._icon_pixmap = None

        # Resolve label: per-state label > button label > icon-only > text fallback
        if state_label:
            self.setText(state_label)
        elif self._config.label:
            self.setText(self._config.label)
        elif self._icon_pixmap:
            self.setText("")
        else:
            # Unicode fallback when no icon available
            if command == "play_pause":
                self.setText("\u23f8" if active else "\u25b6")
            elif command == "mute":
                self.setText("\U0001f507" if active else "\U0001f50a")

        self._scaled_icon = None
        self._scaled_icon_size = 0
        self.update()

    def update_media_state(self, is_playing: bool) -> None:
        """Update icon/label for play_pause buttons based on playback state."""
        self._media_is_playing = is_playing
        self._update_media_toggle("play_pause")

    def update_mute_state(self, is_muted: bool) -> None:
        """Update icon/label for mute buttons based on mute state."""
        self._media_is_muted = is_muted
        self._update_media_toggle("mute")

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
