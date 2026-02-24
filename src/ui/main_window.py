from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from enum import IntFlag, auto

from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QCursor, QMouseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSlider, QSplitter,
)

from ..config.models import ActionConfig, AppConfig, ButtonConfig, FolderConfig
from .styles import DARK_THEME, TITLE_BAR_STYLE

if TYPE_CHECKING:
    from ..config.manager import ConfigManager
    from ..actions.registry import ActionRegistry

logger = logging.getLogger(__name__)


class TitleBar(QWidget):
    """Custom frameless title bar with drag support and opacity slider."""

    def __init__(self, parent: MainWindow) -> None:
        super().__init__(parent)
        self._main_window = parent
        self._drag_pos: QPoint | None = None
        self.setObjectName("titleBar")
        self.setStyleSheet(TITLE_BAR_STYLE)
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(4)

        self._title_label = QLabel("SteamDeckSoft")
        self._title_label.setStyleSheet("color: #e94560; font-size: 13px; font-weight: bold;")
        layout.addWidget(self._title_label)

        # Folder tree toggle button
        btn_style = (
            "QPushButton { background: transparent; color: #a0a0a0; border: none; font-size: 13px; }"
            "QPushButton:hover { background-color: #2a2a4a; color: #ffffff; border-radius: 4px; }"
        )

        self._tree_toggle_btn = QPushButton("\u2630")  # ☰
        self._tree_toggle_btn.setFixedSize(28, 24)
        self._tree_toggle_btn.setStyleSheet(btn_style)
        self._tree_toggle_btn.setToolTip("Toggle folder tree")
        self._tree_toggle_btn.clicked.connect(self._main_window.toggle_folder_tree)
        layout.addWidget(self._tree_toggle_btn)

        layout.addStretch()

        # Opacity slider
        opacity_label = QLabel("\u25d0")
        opacity_label.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        opacity_label.setToolTip("Window opacity")
        layout.addWidget(opacity_label)

        opacity_pct = int(self._main_window._config_manager.settings.window_opacity * 100)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(20, 100)
        self._opacity_slider.setValue(opacity_pct)
        self._opacity_slider.setFixedWidth(80)
        self._opacity_slider.setFixedHeight(18)
        self._opacity_slider.setToolTip(f"Opacity: {opacity_pct}%")
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self._opacity_slider)

        tray_btn = QPushButton("\u23cf")
        tray_btn.setFixedSize(28, 24)
        tray_btn.setStyleSheet(btn_style)
        tray_btn.setToolTip("Minimize to tray")
        tray_btn.clicked.connect(self._main_window._minimize_to_tray)
        layout.addWidget(tray_btn)

        minimize_btn = QPushButton("\u2014")
        minimize_btn.setFixedSize(28, 24)
        minimize_btn.setStyleSheet(btn_style)
        minimize_btn.setToolTip("Minimize")
        minimize_btn.clicked.connect(self._main_window.showMinimized)
        layout.addWidget(minimize_btn)

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(28, 24)
        close_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #a0a0a0; border: none; font-size: 13px; }"
            "QPushButton:hover { background-color: #e94560; color: #ffffff; border-radius: 4px; }"
        )
        close_btn.setToolTip("Quit")
        close_btn.clicked.connect(self._main_window._quit_app)
        layout.addWidget(close_btn)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _on_opacity_changed(self, value: int) -> None:
        self._opacity_slider.setToolTip(f"Opacity: {value}%")
        self._main_window.set_opacity(value / 100.0)

    def _show_context_menu(self, pos) -> None:
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        settings_action = menu.addAction("Settings")
        menu.addSeparator()
        export_action = menu.addAction("Export Config")
        import_action = menu.addAction("Import Config")
        action = menu.exec(self.mapToGlobal(pos))
        if action == settings_action:
            from .settings_dialog import SettingsDialog
            dialog = SettingsDialog(self._main_window._config_manager, self._main_window)
            if dialog.exec():
                self._main_window.reload_config()
        elif action == export_action:
            self._export_config()
        elif action == import_action:
            self._import_config()

    def _export_config(self) -> None:
        from pathlib import Path
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Config", "steamdecksoft_config.json",
            "JSON Files (*.json)",
        )
        if not path:
            return
        try:
            self._main_window._config_manager.export_config(Path(path))
            QMessageBox.information(self, "Export Config", "Config exported successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Export Config", f"Failed to export config:\n{e}")

    def _import_config(self) -> None:
        from pathlib import Path
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Config", "",
            "JSON Files (*.json)",
        )
        if not path:
            return
        reply = QMessageBox.question(
            self, "Import Config",
            "This will replace your current config.\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._main_window._config_manager.import_config(Path(path))
            self._main_window.reload_config()
            QMessageBox.information(self, "Import Config", "Config imported successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Import Config", f"Failed to import config:\n{e}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._main_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._main_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None


class _Edge(IntFlag):
    NONE = 0
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()


_EDGE_CURSORS = {
    _Edge.LEFT: Qt.CursorShape.SizeHorCursor,
    _Edge.RIGHT: Qt.CursorShape.SizeHorCursor,
    _Edge.TOP: Qt.CursorShape.SizeVerCursor,
    _Edge.BOTTOM: Qt.CursorShape.SizeVerCursor,
    _Edge.TOP | _Edge.LEFT: Qt.CursorShape.SizeFDiagCursor,
    _Edge.BOTTOM | _Edge.RIGHT: Qt.CursorShape.SizeFDiagCursor,
    _Edge.TOP | _Edge.RIGHT: Qt.CursorShape.SizeBDiagCursor,
    _Edge.BOTTOM | _Edge.LEFT: Qt.CursorShape.SizeBDiagCursor,
}


class MainWindow(QMainWindow):
    _RESIZE_MARGIN = 6

    def __init__(
        self,
        config_manager: ConfigManager,
        action_registry: ActionRegistry,
    ) -> None:
        super().__init__()
        self._config_manager = config_manager
        self._action_registry = action_registry
        self._current_folder_id: str = "root"
        self._buttons: dict[tuple[int, int], object] = {}
        self._folder_tree = None
        self._window_monitor = None
        self._system_stats_service = None
        self._input_detector = None

        self._resize_edge = _Edge.NONE
        self._resize_start_pos: QPoint | None = None
        self._resize_start_geo: QRect | None = None

        self._setup_window()
        self._build_ui()

    def _setup_window(self) -> None:
        self.setWindowTitle("SteamDeckSoft")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)
        self.setStyleSheet(DARK_THEME)

        settings = self._config_manager.settings
        self._apply_size(settings)
        self.setWindowOpacity(settings.window_opacity)

    def _apply_size(self, settings=None) -> None:
        if settings is None:
            settings = self._config_manager.settings
        tree_width = 180 if settings.folder_tree_visible else 0
        width = (
            settings.grid_cols * (settings.button_size + settings.button_spacing)
            + settings.button_spacing + 16 + tree_width
        )
        height = (
            30  # title bar
            + settings.grid_rows * (settings.button_size + settings.button_spacing)
            + settings.button_spacing
            + 16  # margins
        )
        self.setMinimumSize(width, height)
        self.resize(width, height)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        self._title_bar = TitleBar(self)
        main_layout.addWidget(self._title_bar)

        # Splitter: folder tree | grid
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(2)

        # Folder tree
        from .folder_tree import FolderTreeWidget
        self._folder_tree = FolderTreeWidget(self._config_manager, self)
        self._folder_tree.folder_selected.connect(self.switch_to_folder_id)
        self._splitter.addWidget(self._folder_tree)

        # Button grid container
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        settings = self._config_manager.settings
        spacing = settings.button_spacing
        self._grid_layout.setSpacing(spacing)
        self._grid_layout.setContentsMargins(spacing, spacing, spacing, spacing)
        self._splitter.addWidget(self._grid_container)

        # Splitter sizing: tree gets ~180px, grid gets the rest
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([180, 500])

        main_layout.addWidget(self._splitter, 1)

        # Apply tree visibility from settings
        if not settings.folder_tree_visible:
            self._folder_tree.hide()

        # Load initial folder
        self._load_current_folder()

    def _load_current_folder(self) -> None:
        # Clear existing buttons
        for btn in self._buttons.values():
            btn.setParent(None)
            btn.deleteLater()
        self._buttons.clear()

        folder = self._config_manager.get_folder_by_id(self._current_folder_id)
        if folder is None:
            self._current_folder_id = "root"
            folder = self._config_manager.root_folder

        settings = self._config_manager.settings

        from .button_widget import DeckButton

        # Create button map from config
        button_map: dict[tuple[int, int], object] = {}
        for btn_cfg in folder.buttons:
            button_map[btn_cfg.position] = btn_cfg

        # Auto-generate back button at (0,0) for non-root folders
        if self._current_folder_id != "root":
            parent = self._config_manager.find_parent_folder(self._current_folder_id)
            if parent is not None:
                button_map[(0, 0)] = ButtonConfig(
                    position=(0, 0),
                    label="\u2190 Back",
                    action=ActionConfig(type="navigate_folder", params={"folder_id": parent.id}),
                )

        for row in range(settings.grid_rows):
            for col in range(settings.grid_cols):
                btn_cfg = button_map.get((row, col))
                deck_btn = DeckButton(
                    row, col, btn_cfg, self._action_registry, self, settings.button_size
                )
                self._grid_layout.addWidget(deck_btn, row, col)
                self._buttons[(row, col)] = deck_btn

    def switch_to_folder_id(self, folder_id: str) -> None:
        folder = self._config_manager.get_folder_by_id(folder_id)
        if folder is not None:
            self._current_folder_id = folder_id
            self._load_current_folder()
            # Sync tree selection
            if self._folder_tree is not None:
                self._folder_tree.select_folder_by_id(folder_id)
            logger.info("Switched to folder: %s", folder.name)

    def get_current_folder_id(self) -> str:
        return self._current_folder_id

    def toggle_folder_tree(self) -> None:
        if self._folder_tree is None:
            return
        visible = not self._folder_tree.isVisible()
        self._folder_tree.setVisible(visible)
        self._config_manager.settings.folder_tree_visible = visible
        self._config_manager.save()
        self._apply_size()

    def set_input_detector(self, detector) -> None:
        self._input_detector = detector

    def set_window_monitor(self, monitor) -> None:
        self._window_monitor = monitor

    def set_system_stats_service(self, service) -> None:
        self._system_stats_service = service

    def update_monitor_button(self, cpu: float, ram: float) -> None:
        for btn in self._buttons.values():
            btn.update_monitor_data(cpu, ram)

    def show_on_primary(self) -> None:
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y()
        self.move(x, y)
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Reinforce WS_EX_NOACTIVATE so clicks never steal focus
        import ctypes
        GWL_EXSTYLE = -20
        WS_EX_NOACTIVATE = 0x08000000
        hwnd = int(self.winId())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if not (style & WS_EX_NOACTIVATE):
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE
            )

    def toggle_visibility(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self._minimize_to_tray()
        else:
            self.show_on_primary()

    def _minimize_to_tray(self) -> None:
        self.hide()

    def _quit_app(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()

    def _resize_for_settings(self) -> None:
        settings = self._config_manager.settings
        self._apply_size(settings)
        self.setWindowOpacity(settings.window_opacity)
        self._load_current_folder()

    def reload_config(self) -> None:
        self._resize_for_settings()
        if self._folder_tree:
            self._folder_tree.rebuild()
        self._load_current_folder()

    def on_global_numpad(self, row: int, col: int) -> None:
        """Slot for global numpad key presses (Num Lock OFF, via InputDetector hook)."""
        btn = self._buttons.get((row, col))
        if btn is not None:
            btn.animateClick()

    # --- Opacity -------------------------------------------------------

    def set_opacity(self, value: float) -> None:
        value = max(0.2, min(1.0, value))
        self.setWindowOpacity(value)
        self._config_manager.settings.window_opacity = value
        self._config_manager.save()

    # --- Edge resize ---------------------------------------------------

    def _get_resize_edge(self, pos: QPoint) -> _Edge:
        """Return which resize edge(s) the position falls on."""
        m = self._RESIZE_MARGIN
        w, h = self.width(), self.height()
        edge = _Edge.NONE

        if pos.x() < m:
            edge |= _Edge.LEFT
        elif pos.x() > w - m:
            edge |= _Edge.RIGHT

        if pos.y() < m:
            edge |= _Edge.TOP
        elif pos.y() > h - m:
            edge |= _Edge.BOTTOM

        return edge

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.position().toPoint())
            if edge != _Edge.NONE:
                self._resize_edge = edge
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geo = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._resize_edge != _Edge.NONE and self._resize_start_pos is not None:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            geo = QRect(self._resize_start_geo)
            min_w, min_h = self.minimumWidth(), self.minimumHeight()

            if self._resize_edge & _Edge.LEFT:
                new_left = geo.left() + delta.x()
                if geo.right() - new_left + 1 >= min_w:
                    geo.setLeft(new_left)
            if self._resize_edge & _Edge.RIGHT:
                geo.setRight(geo.right() + delta.x())
            if self._resize_edge & _Edge.TOP:
                new_top = geo.top() + delta.y()
                if geo.bottom() - new_top + 1 >= min_h:
                    geo.setTop(new_top)
            if self._resize_edge & _Edge.BOTTOM:
                geo.setBottom(geo.bottom() + delta.y())

            if geo.width() >= min_w and geo.height() >= min_h:
                self.setGeometry(geo)
            event.accept()
            return

        # Update cursor when hovering edges
        edge = self._get_resize_edge(event.position().toPoint())
        cursor = _EDGE_CURSORS.get(edge)
        if cursor is not None:
            self.setCursor(cursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._resize_edge != _Edge.NONE:
            self._resize_edge = _Edge.NONE
            self._resize_start_pos = None
            self._resize_start_geo = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def closeEvent(self, event) -> None:
        event.ignore()
        self._minimize_to_tray()
