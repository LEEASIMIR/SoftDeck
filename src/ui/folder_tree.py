from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal, Qt, QPoint
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QAbstractItemView

if TYPE_CHECKING:
    from ..config.manager import ConfigManager
    from ..config.models import FolderConfig

logger = logging.getLogger(__name__)


class FolderTreeWidget(QTreeWidget):
    folder_selected = pyqtSignal(str)  # folder_id

    def __init__(self, config_manager: ConfigManager, parent=None) -> None:
        super().__init__(parent)
        self._config_manager = config_manager
        self._main_window = parent

        self.setObjectName("folderTree")
        self.setStyleSheet(self._main_window._theme.folder_tree_style)
        self.setHeaderLabel("Folders")
        self.setMinimumWidth(160)
        self.setMaximumWidth(300)

        # Drag and drop
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemClicked.connect(self._on_item_clicked)

        self.rebuild()

    def rebuild(self) -> None:
        self.clear()
        root_folder = self._config_manager.root_folder
        root_item = self._create_item(root_folder)
        self.addTopLevelItem(root_item)
        root_item.setExpanded(True)
        self._restore_expanded(root_item, root_folder)

        # Select root if nothing else selected
        if self.currentItem() is None:
            self.setCurrentItem(root_item)

    def _create_item(self, folder: FolderConfig) -> QTreeWidgetItem:
        btn_count = len(folder.buttons)
        label = f"{folder.name} ({btn_count})" if btn_count else folder.name
        item = QTreeWidgetItem([label])
        item.setData(0, Qt.ItemDataRole.UserRole, folder.id)

        # Root is not draggable
        if folder.id == "root":
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        else:
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsDropEnabled
            )

        for child in folder.children:
            child_item = self._create_item(child)
            item.addChild(child_item)

        return item

    def _restore_expanded(self, item: QTreeWidgetItem, folder: FolderConfig) -> None:
        item.setExpanded(folder.expanded)
        for i in range(item.childCount()):
            child_item = item.child(i)
            child_id = child_item.data(0, Qt.ItemDataRole.UserRole)
            child_folder = self._config_manager.get_folder_by_id(child_id)
            if child_folder:
                self._restore_expanded(child_item, child_folder)

    def select_folder_by_id(self, folder_id: str) -> None:
        item = self._find_item_by_id(folder_id)
        if item is not None:
            self.setCurrentItem(item)
            # Expand parents
            parent = item.parent()
            while parent is not None:
                parent.setExpanded(True)
                parent = parent.parent()

    def _find_item_by_id(self, folder_id: str, item: QTreeWidgetItem | None = None) -> QTreeWidgetItem | None:
        if item is None:
            for i in range(self.topLevelItemCount()):
                result = self._find_item_by_id(folder_id, self.topLevelItem(i))
                if result is not None:
                    return result
            return None

        if item.data(0, Qt.ItemDataRole.UserRole) == folder_id:
            return item
        for i in range(item.childCount()):
            result = self._find_item_by_id(folder_id, item.child(i))
            if result is not None:
                return result
        return None

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        if folder_id:
            self.folder_selected.emit(folder_id)

    def _show_context_menu(self, pos: QPoint) -> None:
        item = self.itemAt(pos)
        if item is None:
            return

        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        is_root = folder_id == "root"

        menu = QMenu(self)
        new_action = menu.addAction("New Sub-Folder")
        rename_action = None
        edit_action = None
        delete_action = None

        if not is_root:
            rename_action = menu.addAction("Rename")
        edit_action = menu.addAction("Edit (Mapped Apps)")
        if not is_root:
            menu.addSeparator()
            delete_action = menu.addAction("Delete")

        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action is None:
            return

        if action == new_action:
            self._add_subfolder(folder_id)
        elif action == rename_action:
            self._rename_folder(folder_id)
        elif action == edit_action:
            self._edit_folder(folder_id)
        elif action == delete_action:
            self._delete_folder(folder_id)

    def _set_passthrough(self, value: bool) -> None:
        if self._main_window is not None and hasattr(self._main_window, "set_numpad_passthrough"):
            self._main_window.set_numpad_passthrough(value)

    def _add_subfolder(self, parent_id: str) -> None:
        self._set_passthrough(True)
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        self._set_passthrough(False)
        if ok and name.strip():
            new_folder = self._config_manager.add_folder(parent_id, name.strip())
            if new_folder:
                self.rebuild()
                self.select_folder_by_id(new_folder.id)
                self.folder_selected.emit(new_folder.id)

    def _rename_folder(self, folder_id: str) -> None:
        folder = self._config_manager.get_folder_by_id(folder_id)
        if folder is None:
            return
        self._set_passthrough(True)
        name, ok = QInputDialog.getText(self, "Rename Folder", "New name:", text=folder.name)
        self._set_passthrough(False)
        if ok and name.strip():
            self._config_manager.rename_folder(folder_id, name.strip())
            self.rebuild()
            self.select_folder_by_id(folder_id)

    def _edit_folder(self, folder_id: str) -> None:
        folder = self._config_manager.get_folder_by_id(folder_id)
        if folder is None:
            return
        from .folder_editor_dialog import FolderEditorDialog
        dialog = FolderEditorDialog(folder, self)
        self._set_passthrough(True)
        result = dialog.exec()
        self._set_passthrough(False)
        if result:
            updated = dialog.get_config()
            folder.name = updated.name
            folder.mapped_apps = updated.mapped_apps
            self._config_manager.save()
            self.rebuild()
            self.select_folder_by_id(folder_id)

    def _delete_folder(self, folder_id: str) -> None:
        if self._config_manager.delete_folder(folder_id):
            self.rebuild()
            # Select root after deletion
            self.select_folder_by_id("root")
            self.folder_selected.emit("root")

    def dropEvent(self, event) -> None:
        """Handle drag-and-drop to move folders in the config."""
        source_item = self.currentItem()
        if source_item is None:
            event.ignore()
            return

        source_id = source_item.data(0, Qt.ItemDataRole.UserRole)
        if source_id == "root":
            event.ignore()
            return

        # Determine drop target
        target_item = self.itemAt(event.position().toPoint())
        if target_item is None:
            event.ignore()
            return

        target_id = target_item.data(0, Qt.ItemDataRole.UserRole)

        # Perform the move in config
        if self._config_manager.move_folder(source_id, target_id):
            # Save expanded states before rebuild
            self._save_expanded_states()
            self.rebuild()
            self.select_folder_by_id(source_id)
        else:
            event.ignore()
            return

        # Don't call super — we handle the move ourselves
        event.accept()

    def _save_expanded_states(self) -> None:
        """Persist expanded states from tree items back to config."""
        for i in range(self.topLevelItemCount()):
            self._save_item_expanded(self.topLevelItem(i))

    def _save_item_expanded(self, item: QTreeWidgetItem) -> None:
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        folder = self._config_manager.get_folder_by_id(folder_id)
        if folder:
            folder.expanded = item.isExpanded()
        for i in range(item.childCount()):
            self._save_item_expanded(item.child(i))
