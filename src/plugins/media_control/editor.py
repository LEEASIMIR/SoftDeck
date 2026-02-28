from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QComboBox, QLineEdit, QPushButton, QGroupBox, QFileDialog,
)

from ..base import PluginEditorWidget

MEDIA_COMMANDS = [
    ("play_pause", "Play / Pause"),
    ("next_track", "Next Track"),
    ("prev_track", "Previous Track"),
    ("stop", "Stop"),
    ("volume_up", "Volume Up"),
    ("volume_down", "Volume Down"),
    ("mute", "Mute / Unmute"),
]

# Per-state toggle commands: (command, group_title, state_a_prefix, state_b_prefix)
_TOGGLE_COMMANDS = {
    "play_pause": ("Play / Pause Settings", "Play", "Pause"),
    "mute": ("Mute / Unmute Settings", "Mute", "Unmute"),
}


class MediaControlEditorWidget(PluginEditorWidget):
    def __init__(self) -> None:
        self._combo: QComboBox | None = None
        # Per-state groups: command → (group, a_icon, a_label, b_icon, b_label)
        self._toggle_groups: dict[str, tuple[
            QGroupBox, QLineEdit, QLineEdit, QLineEdit, QLineEdit,
        ]] = {}

    def create_widget(self, parent: QWidget | None = None) -> QWidget:
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        form = QFormLayout()
        self._combo = QComboBox()
        for value, label in MEDIA_COMMANDS:
            self._combo.addItem(label, value)
        form.addRow("Command:", self._combo)
        layout.addLayout(form)

        # Build per-state groups for toggle commands
        for cmd, (title, prefix_a, prefix_b) in _TOGGLE_COMMANDS.items():
            group = QGroupBox(title)
            gf = QFormLayout(group)

            a_icon = QLineEdit()
            a_icon.setPlaceholderText("(default icon)")
            a_row = QHBoxLayout()
            a_row.addWidget(a_icon)
            a_browse = QPushButton("Browse...")
            a_browse.clicked.connect(lambda _=False, e=a_icon: self._browse_icon(e))
            a_row.addWidget(a_browse)
            gf.addRow(f"{prefix_a} Icon:", a_row)

            a_label = QLineEdit()
            a_label.setPlaceholderText("(optional)")
            gf.addRow(f"{prefix_a} Label:", a_label)

            b_icon = QLineEdit()
            b_icon.setPlaceholderText("(default icon)")
            b_row = QHBoxLayout()
            b_row.addWidget(b_icon)
            b_browse = QPushButton("Browse...")
            b_browse.clicked.connect(lambda _=False, e=b_icon: self._browse_icon(e))
            b_row.addWidget(b_browse)
            gf.addRow(f"{prefix_b} Icon:", b_row)

            b_label = QLineEdit()
            b_label.setPlaceholderText("(optional)")
            gf.addRow(f"{prefix_b} Label:", b_label)

            layout.addWidget(group)
            self._toggle_groups[cmd] = (group, a_icon, a_label, b_icon, b_label)

        # Toggle visibility based on command selection
        self._combo.currentIndexChanged.connect(self._on_command_changed)
        self._on_command_changed(0)

        return widget

    def _on_command_changed(self, _index: int) -> None:
        if self._combo is None:
            return
        current = self._combo.currentData()
        for cmd, (group, *_) in self._toggle_groups.items():
            group.setVisible(current == cmd)

    def _browse_icon(self, line_edit: QLineEdit | None) -> None:
        if line_edit is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            None, "Select Icon", "", "Images (*.png *.jpg *.svg *.ico)"
        )
        if path:
            line_edit.setText(path)

    # param keys per toggle command: (a_icon, a_label, b_icon, b_label)
    _PARAM_KEYS = {
        "play_pause": ("play_icon", "play_label", "pause_icon", "pause_label"),
        "mute": ("mute_icon", "mute_label", "unmute_icon", "unmute_label"),
    }

    def load_params(self, params: dict[str, Any]) -> None:
        if self._combo is None:
            return
        cmd = params.get("command", "")
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == cmd:
                self._combo.setCurrentIndex(i)
                break
        # Load per-state fields
        for toggle_cmd, keys in self._PARAM_KEYS.items():
            entry = self._toggle_groups.get(toggle_cmd)
            if entry is None:
                continue
            _, a_icon, a_label, b_icon, b_label = entry
            a_icon.setText(params.get(keys[0], ""))
            a_label.setText(params.get(keys[1], ""))
            b_icon.setText(params.get(keys[2], ""))
            b_label.setText(params.get(keys[3], ""))

    def get_params(self) -> dict[str, Any]:
        if self._combo is None:
            return {}
        command = self._combo.currentData()
        params: dict[str, Any] = {"command": command}
        # Include per-state params for toggle commands
        keys = self._PARAM_KEYS.get(command)
        entry = self._toggle_groups.get(command)
        if keys and entry:
            _, a_icon, a_label, b_icon, b_label = entry
            for key, edit in zip(keys, [a_icon, a_label, b_icon, b_label]):
                val = edit.text().strip()
                if val:
                    params[key] = val
        return params
