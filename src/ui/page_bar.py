from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMenu

from .styles import PAGE_BAR_STYLE

if TYPE_CHECKING:
    from ..config.manager import ConfigManager
    from .main_window import MainWindow

logger = logging.getLogger(__name__)


class PageBar(QWidget):
    page_selected = pyqtSignal(int)

    def __init__(self, config_manager: ConfigManager, main_window: MainWindow) -> None:
        super().__init__()
        self._config_manager = config_manager
        self._main_window = main_window
        self._tab_buttons: list[QPushButton] = []
        self._current_index = 0

        self.setObjectName("pageBar")
        self.setStyleSheet(PAGE_BAR_STYLE)
        self.setFixedHeight(36)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(4)

        self.rebuild()

    def rebuild(self) -> None:
        # Clear existing buttons
        for btn in self._tab_buttons:
            btn.setParent(None)
            btn.deleteLater()
        self._tab_buttons.clear()

        # Remove stretch if any
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()

        pages = self._config_manager.pages
        for i, page in enumerate(pages):
            btn = QPushButton(page.name)
            btn.setFixedHeight(26)
            btn.setMinimumWidth(60)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, idx=i: self._page_context_menu(pos, idx))
            btn.clicked.connect(lambda checked, idx=i: self.page_selected.emit(idx))
            self._layout.addWidget(btn)
            self._tab_buttons.append(btn)

        # Add page button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(26, 26)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #4caf50; border: 1px dashed #4caf50;"
            "border-radius: 4px; font-size: 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1a3a1a; }"
        )
        add_btn.clicked.connect(self._add_page)
        self._layout.addWidget(add_btn)
        self._tab_buttons_add = add_btn

        self._layout.addStretch()
        self._update_tab_styles()

    def set_current_index(self, index: int) -> None:
        self._current_index = index
        self._update_tab_styles()

    def _update_tab_styles(self) -> None:
        for i, btn in enumerate(self._tab_buttons):
            if i == self._current_index:
                btn.setStyleSheet(
                    "QPushButton { background-color: #1a1a2e; color: #e94560;"
                    "border: 1px solid #533483; border-bottom: 2px solid #e94560;"
                    "border-radius: 4px; font-size: 12px; font-weight: bold; padding: 2px 12px; }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton { background-color: #111122; color: #a0a0a0;"
                    "border: 1px solid #0f3460; border-radius: 4px;"
                    "font-size: 12px; padding: 2px 12px; }"
                    "QPushButton:hover { background-color: #16213e; color: #e0e0e0; }"
                )

    def _page_context_menu(self, pos, page_index: int) -> None:
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Page")
        delete_action = menu.addAction("Delete Page")

        sender = self._tab_buttons[page_index]
        action = menu.exec(sender.mapToGlobal(pos))

        if action == edit_action:
            self._edit_page(page_index)
        elif action == delete_action:
            self._delete_page(page_index)

    def _add_page(self) -> None:
        from .page_editor_dialog import PageEditorDialog
        from ..config.models import PageConfig
        import uuid

        new_page = PageConfig(id=f"page_{uuid.uuid4().hex[:8]}", name="New Page")
        dialog = PageEditorDialog(new_page, self._main_window)
        if dialog.exec():
            updated = dialog.get_config()
            self._config_manager.pages.append(updated)
            self._config_manager.save()
            self.rebuild()
            self.page_selected.emit(len(self._config_manager.pages) - 1)

    def _edit_page(self, index: int) -> None:
        from .page_editor_dialog import PageEditorDialog
        page = self._config_manager.pages[index]
        dialog = PageEditorDialog(page, self._main_window)
        if dialog.exec():
            updated = dialog.get_config()
            self._config_manager.pages[index] = updated
            self._config_manager.save()
            self.rebuild()
            self._main_window._load_current_page()

    def _delete_page(self, index: int) -> None:
        pages = self._config_manager.pages
        if len(pages) <= 1:
            return  # Don't delete the last page
        pages.pop(index)
        self._config_manager.save()
        if self._current_index >= len(pages):
            self._current_index = len(pages) - 1
        self.rebuild()
        self.page_selected.emit(self._current_index)
