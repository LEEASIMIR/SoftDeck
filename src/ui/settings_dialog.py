from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QSpinBox, QCheckBox, QComboBox,
    QDialogButtonBox, QGroupBox,
)

if TYPE_CHECKING:
    from ..config.manager import ConfigManager

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent=None) -> None:
        super().__init__(parent)
        self._config_manager = config_manager

        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Grid settings
        grid_group = QGroupBox("Grid Layout")
        grid_form = QFormLayout(grid_group)

        self._rows_spin = QSpinBox()
        self._rows_spin.setRange(1, 10)
        grid_form.addRow("Rows:", self._rows_spin)

        self._cols_spin = QSpinBox()
        self._cols_spin.setRange(1, 10)
        grid_form.addRow("Columns:", self._cols_spin)

        self._size_spin = QSpinBox()
        self._size_spin.setRange(50, 200)
        self._size_spin.setSuffix(" px")
        grid_form.addRow("Button Size:", self._size_spin)

        self._spacing_spin = QSpinBox()
        self._spacing_spin.setRange(2, 20)
        self._spacing_spin.setSuffix(" px")
        grid_form.addRow("Button Spacing:", self._spacing_spin)

        layout.addWidget(grid_group)

        # Behavior
        behavior_group = QGroupBox("Behavior")
        behavior_form = QFormLayout(behavior_group)

        self._auto_switch_check = QCheckBox("Auto-switch pages based on active app")
        behavior_form.addRow(self._auto_switch_check)

        self._always_on_top_check = QCheckBox("Always on top")
        behavior_form.addRow(self._always_on_top_check)

        layout.addWidget(behavior_group)

        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance_group)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Dark", "dark")
        appearance_form.addRow("Theme:", self._theme_combo)

        layout.addWidget(appearance_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_settings(self) -> None:
        s = self._config_manager.settings
        self._rows_spin.setValue(s.grid_rows)
        self._cols_spin.setValue(s.grid_cols)
        self._size_spin.setValue(s.button_size)
        self._spacing_spin.setValue(s.button_spacing)
        self._auto_switch_check.setChecked(s.auto_switch_enabled)
        self._always_on_top_check.setChecked(s.always_on_top)

        for i in range(self._theme_combo.count()):
            if self._theme_combo.itemData(i) == s.theme:
                self._theme_combo.setCurrentIndex(i)
                break

    def _apply_and_accept(self) -> None:
        s = self._config_manager.settings
        s.grid_rows = self._rows_spin.value()
        s.grid_cols = self._cols_spin.value()
        s.button_size = self._size_spin.value()
        s.button_spacing = self._spacing_spin.value()
        s.auto_switch_enabled = self._auto_switch_check.isChecked()
        s.always_on_top = self._always_on_top_check.isChecked()
        s.theme = self._theme_combo.currentData()

        self._config_manager.save()
        self.accept()
