from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QDialogButtonBox, QGroupBox, QFileDialog, QWidget, QStackedWidget,
)

from ..config.models import ButtonConfig, ActionConfig

if TYPE_CHECKING:
    from ..config.manager import ConfigManager

logger = logging.getLogger(__name__)

ACTION_TYPES = [
    ("", "None"),
    ("launch_app", "Launch App"),
    ("hotkey", "Hotkey"),
    ("media_control", "Media Control"),
    ("system_monitor", "System Monitor"),
    ("navigate_page", "Navigate Page"),
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
        self._hotkey_edit = QLineEdit()
        self._hotkey_edit.setPlaceholderText("e.g. ctrl+shift+f")
        hotkey_form.addRow("Keys:", self._hotkey_edit)
        self._params_stack.addWidget(hotkey_page)

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

        # Navigate page
        navigate_page = QWidget()
        navigate_form = QFormLayout(navigate_page)
        self._page_combo = QComboBox()
        navigate_form.addRow("Target Page:", self._page_combo)
        self._params_stack.addWidget(navigate_page)

        action_layout.addWidget(self._params_stack)
        layout.addWidget(action_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_config(self) -> None:
        self._label_edit.setText(self._config.label)
        self._icon_edit.setText(self._config.icon)

        # Load pages into combo
        self._page_combo.clear()
        for page in self._config_manager.pages:
            self._page_combo.addItem(page.name, page.id)

        # Set action type
        action_type = self._config.action.type
        for i in range(self._type_combo.count()):
            if self._type_combo.itemData(i) == action_type:
                self._type_combo.setCurrentIndex(i)
                break

        # Load params
        params = self._config.action.params
        if action_type == "launch_app":
            self._app_path_edit.setText(params.get("path", ""))
            self._app_args_edit.setText(params.get("args", ""))
            self._app_workdir_edit.setText(params.get("working_dir", ""))
        elif action_type == "hotkey":
            self._hotkey_edit.setText(params.get("keys", ""))
        elif action_type == "media_control":
            cmd = params.get("command", "")
            for i in range(self._media_combo.count()):
                if self._media_combo.itemData(i) == cmd:
                    self._media_combo.setCurrentIndex(i)
                    break
        elif action_type == "navigate_page":
            page_id = params.get("page_id", "")
            for i in range(self._page_combo.count()):
                if self._page_combo.itemData(i) == page_id:
                    self._page_combo.setCurrentIndex(i)
                    break

    def _on_type_changed(self, index: int) -> None:
        action_type = self._type_combo.itemData(index)
        type_to_page = {
            "": 0,
            "launch_app": 1,
            "hotkey": 2,
            "media_control": 3,
            "system_monitor": 4,
            "navigate_page": 5,
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
        elif action_type == "media_control":
            params["command"] = self._media_combo.currentData()
        elif action_type == "system_monitor":
            params["display"] = "cpu_ram"
        elif action_type == "navigate_page":
            params["page_id"] = self._page_combo.currentData() or ""

        return ButtonConfig(
            position=(self._row, self._col),
            label=self._label_edit.text(),
            icon=self._icon_edit.text(),
            action=ActionConfig(type=action_type or "", params=params),
        )
