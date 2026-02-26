from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget,
    QDialogButtonBox, QGroupBox, QInputDialog,
)

from ..config.models import FolderConfig

logger = logging.getLogger(__name__)


class FolderEditorDialog(QDialog):
    def __init__(self, folder: FolderConfig, parent=None) -> None:
        super().__init__(parent)
        self._folder = folder

        self.setWindowTitle(f"Edit Folder: {folder.name}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._build_ui()
        self._load_config()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Basic info
        basic_group = QGroupBox("Folder Info")
        basic_form = QFormLayout(basic_group)

        self._name_edit = QLineEdit()
        basic_form.addRow("Name:", self._name_edit)

        self._id_label = QLabel()
        self._id_label.setStyleSheet("font-size: 11px;")
        basic_form.addRow("ID:", self._id_label)

        layout.addWidget(basic_group)

        # App mapping
        mapping_group = QGroupBox("App Mapping (Auto-Switch)")
        mapping_layout = QVBoxLayout(mapping_group)

        mapping_layout.addWidget(QLabel(
            "Add exe names that will auto-switch to this folder.\n"
            "e.g. Code.exe, chrome.exe"
        ))

        self._app_list = QListWidget()
        mapping_layout.addWidget(self._app_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_app)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_app)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        mapping_layout.addLayout(btn_row)

        layout.addWidget(mapping_group)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_config(self) -> None:
        self._name_edit.setText(self._folder.name)
        self._id_label.setText(self._folder.id)
        for app in self._folder.mapped_apps:
            self._app_list.addItem(app)

    def _add_app(self) -> None:
        text, ok = QInputDialog.getText(
            self, "Add App", "Exe name (e.g. Code.exe):"
        )
        if ok and text.strip():
            self._app_list.addItem(text.strip())

    def _remove_app(self) -> None:
        current = self._app_list.currentRow()
        if current >= 0:
            self._app_list.takeItem(current)

    def get_config(self) -> FolderConfig:
        apps = []
        for i in range(self._app_list.count()):
            apps.append(self._app_list.item(i).text())

        return FolderConfig(
            id=self._folder.id,
            name=self._name_edit.text() or "Unnamed",
            mapped_apps=apps,
            buttons=list(self._folder.buttons),
            children=list(self._folder.children),
            expanded=self._folder.expanded,
        )
