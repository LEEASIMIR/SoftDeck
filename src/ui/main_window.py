from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QIcon, QMouseEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy,
)

from ..config.models import AppConfig, PageConfig
from .styles import DARK_THEME, TITLE_BAR_STYLE

if TYPE_CHECKING:
    from ..config.manager import ConfigManager
    from ..actions.registry import ActionRegistry

logger = logging.getLogger(__name__)


class TitleBar(QWidget):
    """Custom frameless title bar with drag support."""

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

        layout.addStretch()

        btn_style = (
            "QPushButton { background: transparent; color: #a0a0a0; border: none; font-size: 13px; }"
            "QPushButton:hover { background-color: #2a2a4a; color: #ffffff; border-radius: 4px; }"
        )

        tray_btn = QPushButton("⏏")
        tray_btn.setFixedSize(28, 24)
        tray_btn.setStyleSheet(btn_style)
        tray_btn.setToolTip("Minimize to tray")
        tray_btn.clicked.connect(self._main_window._minimize_to_tray)
        layout.addWidget(tray_btn)

        minimize_btn = QPushButton("—")
        minimize_btn.setFixedSize(28, 24)
        minimize_btn.setStyleSheet(btn_style)
        minimize_btn.setToolTip("Minimize")
        minimize_btn.clicked.connect(self._main_window.showMinimized)
        layout.addWidget(minimize_btn)

        close_btn = QPushButton("✕")
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

    def _show_context_menu(self, pos) -> None:
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        settings_action = menu.addAction("Settings")
        action = menu.exec(self.mapToGlobal(pos))
        if action == settings_action:
            from .settings_dialog import SettingsDialog
            dialog = SettingsDialog(self._main_window._config_manager, self._main_window)
            if dialog.exec():
                self._main_window.reload_config()

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


class MainWindow(QMainWindow):
    def __init__(
        self,
        config_manager: ConfigManager,
        action_registry: ActionRegistry,
    ) -> None:
        super().__init__()
        self._config_manager = config_manager
        self._action_registry = action_registry
        self._current_page_index = 0
        self._buttons: dict[tuple[int, int], object] = {}
        self._page_bar = None
        self._window_monitor = None
        self._system_stats_service = None
        self._input_detector = None

        self._setup_window()
        self._build_ui()

    def _setup_window(self) -> None:
        self.setWindowTitle("SteamDeckSoft")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(DARK_THEME)

        settings = self._config_manager.settings
        width = settings.grid_cols * (settings.button_size + settings.button_spacing) + settings.button_spacing + 16
        height = (
            30  # title bar
            + settings.grid_rows * (settings.button_size + settings.button_spacing) + settings.button_spacing
            + 36  # page bar
            + 16  # margins
        )
        self.setFixedSize(width, height)

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

        # Button grid container
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        settings = self._config_manager.settings
        spacing = settings.button_spacing
        self._grid_layout.setSpacing(spacing)
        self._grid_layout.setContentsMargins(spacing, spacing, spacing, spacing)
        main_layout.addWidget(self._grid_container, 1)

        # Page bar (will be set up by Phase 2)
        from .page_bar import PageBar
        self._page_bar = PageBar(self._config_manager, self)
        self._page_bar.page_selected.connect(self.switch_to_page_index)
        main_layout.addWidget(self._page_bar)

        # Load initial page
        self._load_current_page()

    def _load_current_page(self) -> None:
        # Clear existing buttons
        for btn in self._buttons.values():
            btn.setParent(None)
            btn.deleteLater()
        self._buttons.clear()

        pages = self._config_manager.pages
        if not pages:
            return

        if self._current_page_index >= len(pages):
            self._current_page_index = 0

        page = pages[self._current_page_index]
        settings = self._config_manager.settings

        from .button_widget import DeckButton

        # Create button map from config
        button_map: dict[tuple[int, int], object] = {}
        for btn_cfg in page.buttons:
            button_map[btn_cfg.position] = btn_cfg

        for row in range(settings.grid_rows):
            for col in range(settings.grid_cols):
                btn_cfg = button_map.get((row, col))
                deck_btn = DeckButton(
                    row, col, btn_cfg, self._action_registry, self, settings.button_size
                )
                self._grid_layout.addWidget(deck_btn, row, col)
                self._buttons[(row, col)] = deck_btn

        # Update page bar selection
        if self._page_bar is not None:
            self._page_bar.set_current_index(self._current_page_index)

    def switch_to_page_index(self, index: int) -> None:
        pages = self._config_manager.pages
        if 0 <= index < len(pages):
            self._current_page_index = index
            self._load_current_page()
            logger.info("Switched to page: %s", pages[index].name)

    def switch_to_page_id(self, page_id: str) -> None:
        for i, page in enumerate(self._config_manager.pages):
            if page.id == page_id:
                self.switch_to_page_index(i)
                return

    def get_current_page_index(self) -> int:
        return self._current_page_index

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
        self.raise_()
        self.activateWindow()

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
        width = settings.grid_cols * (settings.button_size + settings.button_spacing) + settings.button_spacing + 16
        height = (
            30
            + settings.grid_rows * (settings.button_size + settings.button_spacing) + settings.button_spacing
            + 36
            + 16
        )
        self.setFixedSize(width, height)
        self._load_current_page()

    def reload_config(self) -> None:
        self._resize_for_settings()
        if self._page_bar:
            self._page_bar.rebuild()
        self._load_current_page()

    # Numpad-style keyboard shortcuts: 7,8,9 / 4,5,6 / 1,2,3 → top-left 3x3 grid
    _KEY_TO_BUTTON: dict[int, tuple[int, int]] = {
        Qt.Key.Key_7: (0, 0), Qt.Key.Key_8: (0, 1), Qt.Key.Key_9: (0, 2),
        Qt.Key.Key_4: (1, 0), Qt.Key.Key_5: (1, 1), Qt.Key.Key_6: (1, 2),
        Qt.Key.Key_1: (2, 0), Qt.Key.Key_2: (2, 1), Qt.Key.Key_3: (2, 2),
    }

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Ignore software-injected key events (e.g. from keyboard.send())
        if self._input_detector and self._input_detector.last_was_injected:
            return
        pos = self._KEY_TO_BUTTON.get(event.key())
        if pos is not None and not event.isAutoRepeat():
            btn = self._buttons.get(pos)
            if btn is not None:
                btn.animateClick()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        event.ignore()
        self._minimize_to_tray()
