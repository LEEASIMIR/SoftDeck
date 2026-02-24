from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox, QTextEdit,
    QDialogButtonBox, QGroupBox, QFileDialog, QWidget, QStackedWidget,
    QListWidget, QSpinBox, QListWidgetItem,
)

from ..config.models import ButtonConfig, ActionConfig

if TYPE_CHECKING:
    from ..config.manager import ConfigManager

logger = logging.getLogger(__name__)

# Qt key → keyboard library name mapping
_QT_KEY_MAP: dict[int, str] = {
    # Letters
    Qt.Key.Key_A: "a", Qt.Key.Key_B: "b", Qt.Key.Key_C: "c",
    Qt.Key.Key_D: "d", Qt.Key.Key_E: "e", Qt.Key.Key_F: "f",
    Qt.Key.Key_G: "g", Qt.Key.Key_H: "h", Qt.Key.Key_I: "i",
    Qt.Key.Key_J: "j", Qt.Key.Key_K: "k", Qt.Key.Key_L: "l",
    Qt.Key.Key_M: "m", Qt.Key.Key_N: "n", Qt.Key.Key_O: "o",
    Qt.Key.Key_P: "p", Qt.Key.Key_Q: "q", Qt.Key.Key_R: "r",
    Qt.Key.Key_S: "s", Qt.Key.Key_T: "t", Qt.Key.Key_U: "u",
    Qt.Key.Key_V: "v", Qt.Key.Key_W: "w", Qt.Key.Key_X: "x",
    Qt.Key.Key_Y: "y", Qt.Key.Key_Z: "z",
    # Numbers
    Qt.Key.Key_0: "0", Qt.Key.Key_1: "1", Qt.Key.Key_2: "2",
    Qt.Key.Key_3: "3", Qt.Key.Key_4: "4", Qt.Key.Key_5: "5",
    Qt.Key.Key_6: "6", Qt.Key.Key_7: "7", Qt.Key.Key_8: "8",
    Qt.Key.Key_9: "9",
    # Function keys
    Qt.Key.Key_F1: "f1", Qt.Key.Key_F2: "f2", Qt.Key.Key_F3: "f3",
    Qt.Key.Key_F4: "f4", Qt.Key.Key_F5: "f5", Qt.Key.Key_F6: "f6",
    Qt.Key.Key_F7: "f7", Qt.Key.Key_F8: "f8", Qt.Key.Key_F9: "f9",
    Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
    # Navigation
    Qt.Key.Key_Space: "space", Qt.Key.Key_Return: "enter",
    Qt.Key.Key_Enter: "enter", Qt.Key.Key_Tab: "tab",
    Qt.Key.Key_Backspace: "backspace", Qt.Key.Key_Delete: "delete",
    Qt.Key.Key_Insert: "insert",
    Qt.Key.Key_Home: "home", Qt.Key.Key_End: "end",
    Qt.Key.Key_PageUp: "page up", Qt.Key.Key_PageDown: "page down",
    Qt.Key.Key_Up: "up", Qt.Key.Key_Down: "down",
    Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right",
    # Symbols
    Qt.Key.Key_Minus: "-", Qt.Key.Key_Equal: "=",
    Qt.Key.Key_BracketLeft: "[", Qt.Key.Key_BracketRight: "]",
    Qt.Key.Key_Semicolon: ";", Qt.Key.Key_Apostrophe: "'",
    Qt.Key.Key_Comma: ",", Qt.Key.Key_Period: ".",
    Qt.Key.Key_Slash: "/", Qt.Key.Key_Backslash: "\\",
    Qt.Key.Key_QuoteLeft: "`",
    # System keys
    Qt.Key.Key_Print: "print screen", Qt.Key.Key_ScrollLock: "scroll lock",
    Qt.Key.Key_Pause: "pause", Qt.Key.Key_CapsLock: "caps lock",
    Qt.Key.Key_NumLock: "num lock",
}

_MODIFIER_KEYS = {
    Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta,
}


class HotkeyRecorderWidget(QWidget):
    """Widget that captures keyboard input and formats it for the keyboard library."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._display = QLineEdit()
        self._display.setReadOnly(True)
        self._display.setPlaceholderText("e.g. ctrl+shift+f")
        layout.addWidget(self._display)

        self._record_btn = QPushButton("Record")
        self._record_btn.setFixedWidth(70)
        self._record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self._record_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedWidth(50)
        self._clear_btn.clicked.connect(self._clear)
        layout.addWidget(self._clear_btn)

        self._recording = False

    def text(self) -> str:
        return self._display.text()

    def setText(self, text: str) -> None:
        self._display.setText(text)

    def _toggle_recording(self) -> None:
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        self._recording = True
        self._record_btn.setText("Stop")
        self._record_btn.setStyleSheet(
            "QPushButton { background-color: #e94560; color: #ffffff; border: 1px solid #e94560; "
            "border-radius: 4px; font-weight: bold; }"
        )
        self._display.setText("")
        self._display.setPlaceholderText("Press keys...")
        self.setFocus()
        self.grabKeyboard()

    def _stop_recording(self) -> None:
        self._recording = False
        self._record_btn.setText("Record")
        self._record_btn.setStyleSheet("")
        self._display.setPlaceholderText("e.g. ctrl+shift+f")
        self.releaseKeyboard()

    def _clear(self) -> None:
        if self._recording:
            self._stop_recording()
        self._display.setText("")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._recording:
            super().keyPressEvent(event)
            return

        key = event.key()

        # Escape cancels recording
        if key == Qt.Key.Key_Escape:
            self._stop_recording()
            return

        # Skip modifier-only presses — just show them as preview
        if key in _MODIFIER_KEYS:
            parts = self._modifier_parts(event.modifiers())
            if parts:
                self._display.setText("+".join(parts) + "+...")
            return

        # Build final hotkey string
        parts = self._modifier_parts(event.modifiers())
        key_name = _QT_KEY_MAP.get(key)
        if key_name is None:
            # Try text() fallback for unmapped keys
            t = event.text().strip()
            if t and t.isprintable():
                key_name = t.lower()

        if key_name:
            parts.append(key_name)
            self._display.setText("+".join(parts))
            self._stop_recording()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if self._recording:
            event.accept()
            return
        super().keyReleaseEvent(event)

    @staticmethod
    def _modifier_parts(modifiers: Qt.KeyboardModifier) -> list[str]:
        parts: list[str] = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            parts.append("windows")
        return parts

ACTION_TYPES = [
    ("", "None"),
    ("launch_app", "Launch App"),
    ("hotkey", "Hotkey"),
    ("text_input", "Text Input"),
    ("media_control", "Media Control"),
    ("system_monitor", "System Monitor"),
    ("navigate_folder", "Navigate Folder"),
    ("macro", "Macro"),
]

MACRO_STEP_TYPES = [
    ("hotkey", "Hotkey"),
    ("text_input", "Text Input"),
    ("delay", "Delay"),
]

MEDIA_COMMANDS = [
    ("play_pause", "Play / Pause"),
    ("next_track", "Next Track"),
    ("prev_track", "Previous Track"),
    ("stop", "Stop"),
    ("volume_up", "Volume Up"),
    ("volume_down", "Volume Down"),
    ("mute", "Mute / Unmute"),
]


class ButtonEditorDialog(QDialog):
    def __init__(
        self,
        config: ButtonConfig | None,
        row: int,
        col: int,
        config_manager: ConfigManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._row = row
        self._col = col
        self._config_manager = config_manager
        self._config = config or ButtonConfig(position=(row, col))

        self.setWindowTitle(f"Edit Button [{row}, {col}]")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._build_ui()
        self._load_config()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Basic info
        basic_group = QGroupBox("Button")
        basic_form = QFormLayout(basic_group)

        self._label_edit = QLineEdit()
        basic_form.addRow("Label:", self._label_edit)

        icon_row = QHBoxLayout()
        self._icon_edit = QLineEdit()
        icon_browse = QPushButton("Browse...")
        icon_browse.clicked.connect(self._browse_icon)
        icon_row.addWidget(self._icon_edit)
        icon_row.addWidget(icon_browse)
        basic_form.addRow("Icon:", icon_row)

        layout.addWidget(basic_group)

        # Action type
        action_group = QGroupBox("Action")
        action_layout = QVBoxLayout(action_group)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self._type_combo = QComboBox()
        for value, label in ACTION_TYPES:
            self._type_combo.addItem(label, value)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self._type_combo, 1)
        action_layout.addLayout(type_row)

        # Stacked params
        self._params_stack = QStackedWidget()

        # None page
        self._params_stack.addWidget(QWidget())

        # Launch app page
        launch_page = QWidget()
        launch_form = QFormLayout(launch_page)
        self._app_path_edit = QLineEdit()
        path_row = QHBoxLayout()
        path_row.addWidget(self._app_path_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_app)
        path_row.addWidget(browse_btn)
        launch_form.addRow("Path:", path_row)
        self._app_args_edit = QLineEdit()
        launch_form.addRow("Arguments:", self._app_args_edit)
        self._app_workdir_edit = QLineEdit()
        launch_form.addRow("Working Dir:", self._app_workdir_edit)
        self._params_stack.addWidget(launch_page)

        # Hotkey page
        hotkey_page = QWidget()
        hotkey_form = QFormLayout(hotkey_page)
        self._hotkey_edit = HotkeyRecorderWidget()
        hotkey_form.addRow("Keys:", self._hotkey_edit)
        self._params_stack.addWidget(hotkey_page)

        # Text input page
        text_input_page = QWidget()
        text_input_form = QFormLayout(text_input_page)
        self._text_input_edit = QTextEdit()
        self._text_input_edit.setPlaceholderText("Enter text to type...")
        self._text_input_edit.setMaximumHeight(120)
        text_input_form.addRow("Text:", self._text_input_edit)
        self._text_clipboard_check = QCheckBox("Paste via clipboard (Ctrl+V)")
        self._text_clipboard_check.setToolTip(
            "Checked: copies text to clipboard and pastes with Ctrl+V (fast, preserves special characters)\n"
            "Unchecked: types each character sequentially (slower, simulates real typing)"
        )
        text_input_form.addRow(self._text_clipboard_check)
        self._params_stack.addWidget(text_input_page)

        # Media control page
        media_page = QWidget()
        media_form = QFormLayout(media_page)
        self._media_combo = QComboBox()
        for value, label in MEDIA_COMMANDS:
            self._media_combo.addItem(label, value)
        media_form.addRow("Command:", self._media_combo)
        self._params_stack.addWidget(media_page)

        # System monitor page
        monitor_page = QWidget()
        monitor_form = QFormLayout(monitor_page)
        monitor_form.addRow(QLabel("Shows CPU/RAM usage in real-time."))
        self._params_stack.addWidget(monitor_page)

        # Navigate folder page
        navigate_page = QWidget()
        navigate_form = QFormLayout(navigate_page)
        self._folder_combo = QComboBox()
        navigate_form.addRow("Target Folder:", self._folder_combo)
        self._params_stack.addWidget(navigate_page)

        # Macro page
        macro_page = QWidget()
        macro_layout = QVBoxLayout(macro_page)

        # Step list
        self._macro_step_list = QListWidget()
        self._macro_step_list.currentRowChanged.connect(self._on_macro_step_selected)
        macro_layout.addWidget(self._macro_step_list)

        # Add / Remove / Move buttons
        step_btn_row = QHBoxLayout()
        self._macro_add_type = QComboBox()
        for value, label in MACRO_STEP_TYPES:
            self._macro_add_type.addItem(label, value)
        step_btn_row.addWidget(self._macro_add_type)
        add_step_btn = QPushButton("Add")
        add_step_btn.clicked.connect(self._macro_add_step)
        step_btn_row.addWidget(add_step_btn)
        del_step_btn = QPushButton("Delete")
        del_step_btn.clicked.connect(self._macro_del_step)
        step_btn_row.addWidget(del_step_btn)
        up_step_btn = QPushButton("\u25B2")
        up_step_btn.setFixedWidth(30)
        up_step_btn.clicked.connect(self._macro_move_up)
        step_btn_row.addWidget(up_step_btn)
        down_step_btn = QPushButton("\u25BC")
        down_step_btn.setFixedWidth(30)
        down_step_btn.clicked.connect(self._macro_move_down)
        step_btn_row.addWidget(down_step_btn)
        macro_layout.addLayout(step_btn_row)

        # Step edit area (stacked)
        self._macro_edit_stack = QStackedWidget()

        # Empty / no selection
        self._macro_edit_stack.addWidget(QLabel("Select a step to edit"))

        # Hotkey step editor
        hotkey_step_w = QWidget()
        hotkey_step_form = QFormLayout(hotkey_step_w)
        self._macro_hotkey_edit = HotkeyRecorderWidget()
        self._macro_hotkey_edit._display.textChanged.connect(self._macro_update_current_step)
        hotkey_step_form.addRow("Keys:", self._macro_hotkey_edit)
        self._macro_edit_stack.addWidget(hotkey_step_w)

        # Text input step editor
        text_step_w = QWidget()
        text_step_form = QFormLayout(text_step_w)
        self._macro_text_edit = QTextEdit()
        self._macro_text_edit.setPlaceholderText("Enter text to type...")
        self._macro_text_edit.setMaximumHeight(80)
        self._macro_text_edit.textChanged.connect(self._macro_update_current_step)
        text_step_form.addRow("Text:", self._macro_text_edit)
        self._macro_text_clipboard = QCheckBox("Paste via clipboard (Ctrl+V)")
        self._macro_text_clipboard.stateChanged.connect(self._macro_update_current_step)
        text_step_form.addRow(self._macro_text_clipboard)
        self._macro_edit_stack.addWidget(text_step_w)

        # Delay step editor
        delay_step_w = QWidget()
        delay_step_form = QFormLayout(delay_step_w)
        self._macro_delay_spin = QSpinBox()
        self._macro_delay_spin.setRange(10, 30000)
        self._macro_delay_spin.setValue(100)
        self._macro_delay_spin.setSuffix(" ms")
        self._macro_delay_spin.valueChanged.connect(self._macro_update_current_step)
        delay_step_form.addRow("Delay:", self._macro_delay_spin)
        self._macro_edit_stack.addWidget(delay_step_w)

        macro_layout.addWidget(self._macro_edit_stack)

        self._macro_steps: list[dict] = []
        self._macro_loading = False
        self._params_stack.addWidget(macro_page)

        action_layout.addWidget(self._params_stack)
        layout.addWidget(action_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_folder_combo(self) -> None:
        self._folder_combo.clear()
        for folder, depth in self._config_manager.get_all_folders_flat():
            indent = "\u2003" * depth  # em space for indentation
            prefix = "\u2514 " if depth > 0 else ""
            self._folder_combo.addItem(f"{indent}{prefix}{folder.name}", folder.id)

    def _load_config(self) -> None:
        self._label_edit.setText(self._config.label)
        self._icon_edit.setText(self._config.icon)

        # Load folders into combo
        self._populate_folder_combo()

        # Set action type (handle backward compat: navigate_page → navigate_folder)
        action_type = self._config.action.type
        if action_type == "navigate_page":
            action_type = "navigate_folder"

        for i in range(self._type_combo.count()):
            if self._type_combo.itemData(i) == action_type:
                self._type_combo.setCurrentIndex(i)
                break

        # Load params
        params = self._config.action.params
        orig_type = self._config.action.type
        if orig_type == "launch_app":
            self._app_path_edit.setText(params.get("path", ""))
            self._app_args_edit.setText(params.get("args", ""))
            self._app_workdir_edit.setText(params.get("working_dir", ""))
        elif orig_type == "hotkey":
            self._hotkey_edit.setText(params.get("keys", ""))
        elif orig_type == "text_input":
            self._text_input_edit.setPlainText(params.get("text", ""))
            self._text_clipboard_check.setChecked(params.get("use_clipboard", False))
        elif orig_type == "media_control":
            cmd = params.get("command", "")
            for i in range(self._media_combo.count()):
                if self._media_combo.itemData(i) == cmd:
                    self._media_combo.setCurrentIndex(i)
                    break
        elif orig_type in ("navigate_page", "navigate_folder"):
            folder_id = params.get("folder_id", "") or params.get("page_id", "")
            for i in range(self._folder_combo.count()):
                if self._folder_combo.itemData(i) == folder_id:
                    self._folder_combo.setCurrentIndex(i)
                    break
        elif orig_type == "macro":
            self._macro_steps = [dict(s) for s in params.get("steps", [])]
            self._macro_refresh_list()

    def _on_type_changed(self, index: int) -> None:
        action_type = self._type_combo.itemData(index)
        type_to_page = {
            "": 0,
            "launch_app": 1,
            "hotkey": 2,
            "text_input": 3,
            "media_control": 4,
            "system_monitor": 5,
            "navigate_folder": 6,
            "macro": 7,
        }
        self._params_stack.setCurrentIndex(type_to_page.get(action_type, 0))

    def _browse_icon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon", "", "Images (*.png *.jpg *.svg *.ico)"
        )
        if path:
            self._icon_edit.setText(path)

    def _browse_app(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Application", "", "Executables (*.exe);;All Files (*)"
        )
        if path:
            self._app_path_edit.setText(path)

    def get_config(self) -> ButtonConfig:
        action_type = self._type_combo.currentData()
        params: dict = {}

        if action_type == "launch_app":
            params["path"] = self._app_path_edit.text()
            if self._app_args_edit.text():
                params["args"] = self._app_args_edit.text()
            if self._app_workdir_edit.text():
                params["working_dir"] = self._app_workdir_edit.text()
        elif action_type == "hotkey":
            params["keys"] = self._hotkey_edit.text()
        elif action_type == "text_input":
            params["text"] = self._text_input_edit.toPlainText()
            params["use_clipboard"] = self._text_clipboard_check.isChecked()
        elif action_type == "media_control":
            params["command"] = self._media_combo.currentData()
        elif action_type == "system_monitor":
            params["display"] = "cpu_ram"
        elif action_type == "navigate_folder":
            params["folder_id"] = self._folder_combo.currentData() or ""
        elif action_type == "macro":
            params["steps"] = [dict(s) for s in self._macro_steps]

        return ButtonConfig(
            position=(self._row, self._col),
            label=self._label_edit.text(),
            icon=self._icon_edit.text(),
            action=ActionConfig(type=action_type or "", params=params),
        )

    # --- Macro editor helpers ---

    @staticmethod
    def _macro_step_summary(step: dict) -> str:
        t = step.get("type", "")
        p = step.get("params", {})
        if t == "hotkey":
            return f"Hotkey: {p.get('keys', '')}"
        if t == "text_input":
            text = p.get("text", "")
            clip = " (clipboard)" if p.get("use_clipboard") else ""
            preview = (text[:25] + "...") if len(text) > 25 else text
            return f"Text: {preview}{clip}"
        if t == "delay":
            return f"Delay: {p.get('ms', 100)}ms"
        return f"Unknown: {t}"

    def _macro_refresh_list(self) -> None:
        self._macro_loading = True
        current = self._macro_step_list.currentRow()
        self._macro_step_list.clear()
        for i, step in enumerate(self._macro_steps):
            self._macro_step_list.addItem(f"{i + 1}. {self._macro_step_summary(step)}")
        if 0 <= current < len(self._macro_steps):
            self._macro_step_list.setCurrentRow(current)
        self._macro_loading = False

    def _macro_add_step(self) -> None:
        step_type = self._macro_add_type.currentData()
        if step_type == "hotkey":
            step = {"type": "hotkey", "params": {"keys": ""}}
        elif step_type == "text_input":
            step = {"type": "text_input", "params": {"text": "", "use_clipboard": False}}
        else:
            step = {"type": "delay", "params": {"ms": 100}}
        self._macro_steps.append(step)
        self._macro_refresh_list()
        self._macro_step_list.setCurrentRow(len(self._macro_steps) - 1)

    def _macro_del_step(self) -> None:
        row = self._macro_step_list.currentRow()
        if 0 <= row < len(self._macro_steps):
            self._macro_steps.pop(row)
            self._macro_refresh_list()

    def _macro_move_up(self) -> None:
        row = self._macro_step_list.currentRow()
        if row > 0:
            self._macro_steps[row - 1], self._macro_steps[row] = (
                self._macro_steps[row], self._macro_steps[row - 1]
            )
            self._macro_refresh_list()
            self._macro_step_list.setCurrentRow(row - 1)

    def _macro_move_down(self) -> None:
        row = self._macro_step_list.currentRow()
        if 0 <= row < len(self._macro_steps) - 1:
            self._macro_steps[row], self._macro_steps[row + 1] = (
                self._macro_steps[row + 1], self._macro_steps[row]
            )
            self._macro_refresh_list()
            self._macro_step_list.setCurrentRow(row + 1)

    def _on_macro_step_selected(self, row: int) -> None:
        if self._macro_loading:
            return
        if row < 0 or row >= len(self._macro_steps):
            self._macro_edit_stack.setCurrentIndex(0)
            return

        self._macro_loading = True
        step = self._macro_steps[row]
        step_type = step.get("type", "")
        p = step.get("params", {})

        if step_type == "hotkey":
            self._macro_hotkey_edit.setText(p.get("keys", ""))
            self._macro_edit_stack.setCurrentIndex(1)
        elif step_type == "text_input":
            self._macro_text_edit.setPlainText(p.get("text", ""))
            self._macro_text_clipboard.setChecked(p.get("use_clipboard", False))
            self._macro_edit_stack.setCurrentIndex(2)
        elif step_type == "delay":
            self._macro_delay_spin.setValue(p.get("ms", 100))
            self._macro_edit_stack.setCurrentIndex(3)
        else:
            self._macro_edit_stack.setCurrentIndex(0)
        self._macro_loading = False

    def _macro_update_current_step(self) -> None:
        if self._macro_loading:
            return
        row = self._macro_step_list.currentRow()
        if row < 0 or row >= len(self._macro_steps):
            return

        step = self._macro_steps[row]
        step_type = step.get("type", "")

        if step_type == "hotkey":
            step["params"]["keys"] = self._macro_hotkey_edit.text()
        elif step_type == "text_input":
            step["params"]["text"] = self._macro_text_edit.toPlainText()
            step["params"]["use_clipboard"] = self._macro_text_clipboard.isChecked()
        elif step_type == "delay":
            step["params"]["ms"] = self._macro_delay_spin.value()

        # Update list item text
        item = self._macro_step_list.item(row)
        if item:
            item.setText(f"{row + 1}. {self._macro_step_summary(step)}")
