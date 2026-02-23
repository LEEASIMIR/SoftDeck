DARK_THEME = """
QMainWindow, QDialog {
    background-color: #1a1a2e;
}

QWidget#centralWidget {
    background-color: #1a1a2e;
}

QLabel {
    color: #e0e0e0;
    font-size: 12px;
}

QPushButton {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1a2a50;
    border-color: #533483;
}

QPushButton:pressed {
    background-color: #0f3460;
    border-color: #e94560;
}

QTabBar::tab {
    background-color: #16213e;
    color: #a0a0a0;
    border: 1px solid #0f3460;
    border-bottom: none;
    padding: 6px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 12px;
}

QTabBar::tab:selected {
    background-color: #1a1a2e;
    color: #e94560;
    border-color: #533483;
}

QTabBar::tab:hover:!selected {
    background-color: #1a2a50;
    color: #e0e0e0;
}

QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0f3460;
}

QMenu::separator {
    height: 1px;
    background-color: #0f3460;
    margin: 4px 8px;
}

QLineEdit, QSpinBox, QComboBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #533483;
}

QCheckBox {
    color: #e0e0e0;
    font-size: 12px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #0f3460;
    background-color: #16213e;
}

QCheckBox::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}

QGroupBox {
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-size: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}

QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #533483;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QListWidget {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #0f3460;
    color: #e94560;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
    padding: 6px 16px;
}
"""

DECK_BUTTON_STYLE = """
QPushButton#deckButton {{
    background-color: {bg};
    color: #e0e0e0;
    border: 2px solid #0f3460;
    border-radius: 10px;
    font-size: 11px;
    font-weight: bold;
    padding: 4px;
}}

QPushButton#deckButton:hover {{
    background-color: {hover};
    border-color: #533483;
    color: #ffffff;
}}

QPushButton#deckButton:pressed {{
    background-color: {pressed};
    border-color: #e94560;
}}
"""

DECK_BUTTON_EMPTY_STYLE = """
QPushButton#deckButton {
    background-color: #0d1117;
    color: #404050;
    border: 1px dashed #1e2a3a;
    border-radius: 10px;
    font-size: 11px;
    padding: 4px;
}

QPushButton#deckButton:hover {
    background-color: #131926;
    border-color: #2a3a50;
    color: #606070;
}
"""

MONITOR_BUTTON_STYLE = """
QPushButton#deckButton {
    background-color: #0d1a0d;
    color: #4caf50;
    border: 2px solid #1b5e20;
    border-radius: 10px;
    font-size: 10px;
    font-weight: bold;
    padding: 4px;
}
"""

PAGE_BAR_STYLE = """
QWidget#pageBar {
    background-color: #111122;
    border-top: 1px solid #0f3460;
}
"""

TITLE_BAR_STYLE = """
QWidget#titleBar {
    background-color: #111122;
    border-bottom: 1px solid #0f3460;
}
"""
