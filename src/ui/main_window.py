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
from ..version import APP_VERSION
from .styles import get_theme

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
        self._theme = self._main_window._theme
        self.setStyleSheet(self._theme.title_bar_style)
        self.setFixedHeight(25)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Folder tree toggle button
        p = self._theme.palette
        btn_style = (
            f"QPushButton {{ background: transparent; color: {p.text_dim}; border: none; "
            f"font-size: 8px; padding: 0px; margin: 0px; }}"
            f"QPushButton:hover {{ background-color: {p.titlebar_btn_hover_bg}; color: {p.text_bright}; border-radius: 2px; }}"
        )

        self._tree_toggle_btn = QPushButton("\u2630")  # ☰
        self._tree_toggle_btn.setFixedSize(18, 18)
        self._tree_toggle_btn.setStyleSheet(btn_style)
        self._tree_toggle_btn.setToolTip("Toggle folder tree")
        self._tree_toggle_btn.clicked.connect(self._main_window.toggle_folder_tree)
        layout.addWidget(self._tree_toggle_btn)

        layout.addStretch()

        # Opacity slider
        opacity_label = QLabel("\u25d0")
        opacity_label.setStyleSheet(f"color: {p.text_dim}; font-size: 8px; padding: 0px; margin: 0px;")
        opacity_label.setToolTip("Window opacity")
        layout.addWidget(opacity_label)

        opacity_pct = int(self._main_window._config_manager.settings.window_opacity * 100)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(20, 100)
        self._opacity_slider.setValue(opacity_pct)
        self._opacity_slider.setFixedWidth(40)
        self._opacity_slider.setFixedHeight(12)
        self._opacity_slider.setToolTip(f"Opacity: {opacity_pct}%")
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self._opacity_slider)

        tray_btn = QPushButton("\u25bc")
        tray_btn.setFixedSize(18, 18)
        tray_btn.setStyleSheet(btn_style)
        tray_btn.setToolTip("Minimize to tray")
        tray_btn.clicked.connect(self._main_window._minimize_to_tray)
        layout.addWidget(tray_btn)

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
            self._main_window.set_numpad_passthrough(True)
            result = dialog.exec()
            self._main_window.set_numpad_passthrough(False)
            if result:
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

        self._theme = get_theme(config_manager.settings.theme)

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
        self.setStyleSheet(self._theme.dark_theme)

        settings = self._config_manager.settings
        self._apply_size(settings)
        self.setWindowOpacity(settings.window_opacity)

        if settings.window_x is not None and settings.window_y is not None:
            self.move(settings.window_x, settings.window_y)

    def _apply_size(self, settings=None) -> None:
        if settings is None:
            settings = self._config_manager.settings
        tree_width = 180 if settings.folder_tree_visible else 0
        width = (
            settings.grid_cols * (settings.button_size + settings.button_spacing)
            + settings.button_spacing + 16 + tree_width
        )
        height = (
            25  # title bar
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

        # Version label (bottom-right, barely visible)
        p = self._theme.palette
        self._version_label = QLabel(f"v{APP_VERSION}")
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._version_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: 7px; padding: 0px 4px 2px 0px; background: transparent;"
        )
        main_layout.addWidget(self._version_label)

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
        old_width = self.width()
        visible = not self._folder_tree.isVisible()
        self._folder_tree.setVisible(visible)
        self._config_manager.settings.folder_tree_visible = visible
        self._config_manager.save()
        self._apply_size()
        # Keep right edge fixed — shift x by the width difference
        delta = self.width() - old_width
        if delta != 0:
            self.move(self.x() - delta, self.y())

    def set_input_detector(self, detector) -> None:
        self._input_detector = detector

    def set_numpad_passthrough(self, value: bool) -> None:
        if self._input_detector is not None:
            self._input_detector.set_passthrough(value)

    def set_window_monitor(self, monitor) -> None:
        self._window_monitor = monitor

    def set_system_stats_service(self, service) -> None:
        self._system_stats_service = service

    def update_monitor_button(self, cpu: float, ram: float) -> None:
        for btn in self._buttons.values():
            btn.update_monitor_data(cpu, ram)

    def show_on_primary(self) -> None:
        settings = self._config_manager.settings
        if settings.window_x is not None and settings.window_y is not None:
            self.move(settings.window_x, settings.window_y)
        else:
            self._center_on_primary()
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)

    def _center_on_primary(self) -> None:
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y()
        self.move(x, y)

    def reset_position(self) -> None:
        """Reset window position to center-top of primary screen."""
        self._config_manager.settings.window_x = None
        self._config_manager.settings.window_y = None
        self._config_manager.save()
        self._center_on_primary()

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        pos = event.pos()
        self._config_manager.settings.window_x = pos.x()
        self._config_manager.settings.window_y = pos.y()
        self._config_manager.save()

    # --- Foreground helper for launching external apps ----------------

    def launch_with_foreground(self, callback: object) -> None:
        """Launch an external app ensuring its window appears in front.

        *callback* should be a zero-arg callable that actually starts the
        process (e.g. ``os.startfile(path)``).

        Strategy:
        1. Snapshot all visible window handles.
        2. Temporarily remove WS_EX_NOACTIVATE, attach to the foreground
           thread, call SetForegroundWindow — then execute *callback*.
        3. Restore WS_EX_NOACTIVATE.
        4. Schedule a fallback timer: after 800 ms, find any NEW visible
           window and force it to the visual front via the SetWindowPos
           TOPMOST/NOTOPMOST trick (immune to the foreground lock).
        """
        import ctypes
        from ctypes import wintypes
        from PyQt6.QtCore import QTimer

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        our_hwnd = int(self.winId())

        # -- Step 1: snapshot existing visible windows --------------------
        existing: set[int] = set()
        WNDENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM,
        )

        @WNDENUMPROC
        def _collect(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                existing.add(int(hwnd))
            return True

        user32.EnumWindows(_collect, 0)

        # -- Step 2: claim foreground & launch ----------------------------
        GWL_EXSTYLE = -20
        WS_EX_NOACTIVATE = 0x08000000

        old_style = user32.GetWindowLongW(our_hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            our_hwnd, GWL_EXSTYLE, old_style & ~WS_EX_NOACTIVATE,
        )

        fg = user32.GetForegroundWindow()
        fg_tid = user32.GetWindowThreadProcessId(fg, None)
        our_tid = kernel32.GetCurrentThreadId()

        attached = False
        if fg_tid and fg_tid != our_tid:
            attached = bool(user32.AttachThreadInput(our_tid, fg_tid, True))

        user32.SetForegroundWindow(our_hwnd)

        try:
            callback()
        finally:
            # -- Step 3: restore ------------------------------------------
            if attached:
                user32.AttachThreadInput(our_tid, fg_tid, False)
            user32.SetWindowLongW(our_hwnd, GWL_EXSTYLE, old_style)

        # -- Step 4: fallback — bring new window to front after delay -----
        def _bring_new_to_front():
            found = 0

            @WNDENUMPROC
            def _find(hwnd, _):
                nonlocal found
                h = int(hwnd)
                if (
                    h != our_hwnd
                    and user32.IsWindowVisible(hwnd)
                    and h not in existing
                ):
                    found = h
                    return False
                return True

            user32.EnumWindows(_find, 0)

            if found:
                SWP_NOMOVE_NOSIZE = 0x0001 | 0x0002  # SWP_NOSIZE|SWP_NOMOVE
                HWND_TOPMOST = -1
                HWND_NOTOPMOST = -2
                user32.SetWindowPos(
                    found, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE_NOSIZE,
                )
                user32.SetWindowPos(
                    found, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE_NOSIZE,
                )
                user32.SetForegroundWindow(found)

        QTimer.singleShot(800, _bring_new_to_front)

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
        new_theme_name = self._config_manager.settings.theme
        if new_theme_name != self._theme.palette.name:
            self.apply_theme(new_theme_name)
        self._resize_for_settings()
        if self._folder_tree:
            self._folder_tree.rebuild()
        self._load_current_folder()

    def apply_theme(self, theme_name: str) -> None:
        """Switch to a new theme, updating all stylesheets."""
        self._theme = get_theme(theme_name)

        # Update QApplication global stylesheet
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(self._theme.dark_theme)

        # Update window-level stylesheet
        self.setStyleSheet(self._theme.dark_theme)

        # Rebuild title bar with new palette
        self._title_bar._theme = self._theme
        p = self._theme.palette
        btn_style = (
            f"QPushButton {{ background: transparent; color: {p.text_dim}; border: none; "
            f"font-size: 8px; padding: 0px; margin: 0px; }}"
            f"QPushButton:hover {{ background-color: {p.titlebar_btn_hover_bg}; color: {p.text_bright}; border-radius: 2px; }}"
        )
        self._title_bar.setStyleSheet(self._theme.title_bar_style)
        for child in self._title_bar.findChildren(QPushButton):
            child.setStyleSheet(btn_style)

        # Update folder tree
        if self._folder_tree is not None:
            self._folder_tree.setStyleSheet(self._theme.folder_tree_style)

        # Update version label
        if hasattr(self, '_version_label'):
            self._version_label.setStyleSheet(
                f"color: {p.text_muted}; font-size: 7px; padding: 0px 4px 2px 0px; background: transparent;"
            )

    def on_global_numpad(self, row: int, col: int) -> None:
        """Slot for global numpad key presses (Num Lock OFF, via InputDetector hook)."""
        btn = self._buttons.get((row, col))
        if btn is not None:
            btn.animateClick()

    def navigate_back(self) -> None:
        """Navigate to parent folder. Numpad 0 triggers this."""
        if self._current_folder_id == "root":
            return
        parent = self._config_manager.find_parent_folder(self._current_folder_id)
        if parent is not None:
            self.switch_to_folder_id(parent.id)

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
