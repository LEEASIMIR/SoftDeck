from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePalette:
    """Semantic color palette for a theme."""

    name: str
    display_name: str

    # Background hierarchy (darkest to lightest)
    bg_base: str
    bg_button: str
    bg_titlebar: str
    bg_input: str
    bg_elevated: str
    bg_hover: str
    bg_pressed: str

    # Borders
    border: str
    border_light: str
    border_dark: str

    # Text
    text_primary: str
    text_white: str
    text_bright: str
    text_dim: str
    text_muted: str
    text_empty_hover: str

    # Accent
    accent: str
    accent_hover: str

    # Special
    monitor_green: str
    scrollbar_handle_hover: str

    # Splash
    splash_bg: str
    splash_gradient_end: str

    # Title bar buttons
    titlebar_btn_hover_bg: str


@dataclass(frozen=True)
class ThemeStylesheets:
    """Pre-generated stylesheets for a theme."""

    palette: ThemePalette
    dark_theme: str
    deck_button_style: str
    deck_button_empty_style: str
    monitor_button_style: str
    folder_tree_style: str
    title_bar_style: str


# ---------------------------------------------------------------------------
# Theme Palettes
# ---------------------------------------------------------------------------

THEME_LIGHT = ThemePalette(
    name="light", display_name="Light",
    bg_base="#f2f2f2", bg_button="#e4e4e4", bg_titlebar="#e8e8e8",
    bg_input="#ffffff", bg_elevated="#e0e0e0", bg_hover="#d4d4d4", bg_pressed="#cccccc",
    border="#c0c0c0", border_light="#d0d0d0", border_dark="#b0b0b0",
    text_primary="#333333", text_white="#1a1a1a", text_bright="#000000",
    text_dim="#808080", text_muted="#c8c8c8", text_empty_hover="#a0a0a0",
    accent="#e94560", accent_hover="#ff6b81",
    monitor_green="#2e7d32", scrollbar_handle_hover="#a0a0a0",
    splash_bg="#e8e8e8", splash_gradient_end="#533483",
    titlebar_btn_hover_bg="#d0d0e0",
)

THEME_SOLARIZED_LIGHT = ThemePalette(
    name="solarized_light", display_name="Solarized Light",
    bg_base="#fdf6e3", bg_button="#eee8d5", bg_titlebar="#f0ead8",
    bg_input="#fdf6e3", bg_elevated="#eee8d5", bg_hover="#e4ddc8", bg_pressed="#ddd6c1",
    border="#d3cbb8", border_light="#e0d9c6", border_dark="#c9c1ac",
    text_primary="#586e75", text_white="#073642", text_bright="#002b36",
    text_dim="#93a1a1", text_muted="#d3cbb8", text_empty_hover="#b8b0a0",
    accent="#268bd2", accent_hover="#4a9fe0",
    monitor_green="#859900", scrollbar_handle_hover="#b8b0a0",
    splash_bg="#eee8d5", splash_gradient_end="#6c71c4",
    titlebar_btn_hover_bg="#e0d9c8",
)

THEME_DARK = ThemePalette(
    name="dark", display_name="Dark",
    bg_base="#0e0e0e", bg_button="#0a0a0a", bg_titlebar="#080808",
    bg_input="#141414", bg_elevated="#161616", bg_hover="#222222", bg_pressed="#1a1a1a",
    border="#2a2a2a", border_light="#333333", border_dark="#1a1a1a",
    text_primary="#c0c0c0", text_white="#e0e0e0", text_bright="#ffffff",
    text_dim="#808080", text_muted="#303030", text_empty_hover="#505050",
    accent="#e94560", accent_hover="#ff6b81",
    monitor_green="#4caf50", scrollbar_handle_hover="#404040",
    splash_bg="#0a0a0a", splash_gradient_end="#533483",
    titlebar_btn_hover_bg="#2a2a4a",
)

THEME_MIDNIGHT = ThemePalette(
    name="midnight", display_name="Midnight",
    bg_base="#0d1117", bg_button="#090d12", bg_titlebar="#070a0e",
    bg_input="#131921", bg_elevated="#151c25", bg_hover="#1f2937", bg_pressed="#161d28",
    border="#253040", border_light="#303d50", border_dark="#182030",
    text_primary="#b8c4d0", text_white="#d0dce8", text_bright="#ffffff",
    text_dim="#6b7d8f", text_muted="#2a3545", text_empty_hover="#405060",
    accent="#58a6ff", accent_hover="#79b8ff",
    monitor_green="#4caf50", scrollbar_handle_hover="#354560",
    splash_bg="#090d12", splash_gradient_end="#1a4080",
    titlebar_btn_hover_bg="#1a2a4a",
)

THEME_EMERALD = ThemePalette(
    name="emerald", display_name="Emerald",
    bg_base="#0e1210", bg_button="#0a0e0c", bg_titlebar="#080c0a",
    bg_input="#141a16", bg_elevated="#161c18", bg_hover="#1e2a22", bg_pressed="#182020",
    border="#243028", border_light="#2f3d33", border_dark="#1a241e",
    text_primary="#b8c8be", text_white="#d0e0d6", text_bright="#ffffff",
    text_dim="#708070", text_muted="#283830", text_empty_hover="#406048",
    accent="#4caf50", accent_hover="#66bb6a",
    monitor_green="#4caf50", scrollbar_handle_hover="#355040",
    splash_bg="#0a0e0c", splash_gradient_end="#1a5c20",
    titlebar_btn_hover_bg="#1a3a2a",
)

THEME_VIOLET = ThemePalette(
    name="violet", display_name="Violet",
    bg_base="#110e14", bg_button="#0d0a10", bg_titlebar="#0a080c",
    bg_input="#171420", bg_elevated="#191624", bg_hover="#252030", bg_pressed="#1d1828",
    border="#2e2840", border_light="#3a3350", border_dark="#1e182a",
    text_primary="#c0b8cc", text_white="#d8d0e8", text_bright="#ffffff",
    text_dim="#806e90", text_muted="#302838", text_empty_hover="#483858",
    accent="#bb86fc", accent_hover="#d4a5ff",
    monitor_green="#4caf50", scrollbar_handle_hover="#3a3058",
    splash_bg="#0d0a10", splash_gradient_end="#5c2d91",
    titlebar_btn_hover_bg="#2a1a4a",
)

THEME_NORD = ThemePalette(
    name="nord", display_name="Nord",
    bg_base="#2e3440", bg_button="#272d38", bg_titlebar="#242932",
    bg_input="#353c49", bg_elevated="#383f4d", bg_hover="#434c5e", bg_pressed="#3b4252",
    border="#4c566a", border_light="#5a6580", border_dark="#3b4252",
    text_primary="#d8dee9", text_white="#e5e9f0", text_bright="#eceff4",
    text_dim="#7b88a1", text_muted="#4c566a", text_empty_hover="#5e6b82",
    accent="#88c0d0", accent_hover="#8fbcbb",
    monitor_green="#a3be8c", scrollbar_handle_hover="#5a6578",
    splash_bg="#272d38", splash_gradient_end="#5e81ac",
    titlebar_btn_hover_bg="#3a4560",
)

THEME_DRACULA = ThemePalette(
    name="dracula", display_name="Dracula",
    bg_base="#282a36", bg_button="#21222c", bg_titlebar="#1e1f28",
    bg_input="#2e3040", bg_elevated="#313345", bg_hover="#3a3d50", bg_pressed="#343746",
    border="#44475a", border_light="#545870", border_dark="#383a4c",
    text_primary="#cccce0", text_white="#e0e0f0", text_bright="#f8f8f2",
    text_dim="#6272a4", text_muted="#3a3c50", text_empty_hover="#505368",
    accent="#bd93f9", accent_hover="#caa9fa",
    monitor_green="#50fa7b", scrollbar_handle_hover="#505368",
    splash_bg="#21222c", splash_gradient_end="#6272a4",
    titlebar_btn_hover_bg="#3a3570",
)

THEME_AMBER = ThemePalette(
    name="amber", display_name="Amber",
    bg_base="#100e0c", bg_button="#0c0a08", bg_titlebar="#0a0806",
    bg_input="#181410", bg_elevated="#1a1610", bg_hover="#2a2218", bg_pressed="#201a12",
    border="#362c20", border_light="#443828", border_dark="#221c14",
    text_primary="#c8bcaa", text_white="#e0d4c0", text_bright="#ffffff",
    text_dim="#908070", text_muted="#382e22", text_empty_hover="#584838",
    accent="#ffb74d", accent_hover="#ffc77d",
    monitor_green="#4caf50", scrollbar_handle_hover="#4a3c28",
    splash_bg="#0c0a08", splash_gradient_end="#a06020",
    titlebar_btn_hover_bg="#3a2a1a",
)

THEME_CYBER = ThemePalette(
    name="cyber", display_name="Cyber",
    bg_base="#0a0a0a", bg_button="#060606", bg_titlebar="#040404",
    bg_input="#101010", bg_elevated="#121212", bg_hover="#1e1e1e", bg_pressed="#161616",
    border="#222228", border_light="#303038", border_dark="#161618",
    text_primary="#b0b8c0", text_white="#d0dce0", text_bright="#ffffff",
    text_dim="#606870", text_muted="#282830", text_empty_hover="#404850",
    accent="#00e5ff", accent_hover="#18ffff",
    monitor_green="#4caf50", scrollbar_handle_hover="#353540",
    splash_bg="#060606", splash_gradient_end="#006080",
    titlebar_btn_hover_bg="#0a2a30",
)

THEMES: dict[str, ThemePalette] = {
    "dark": THEME_DARK,
    "light": THEME_LIGHT,
    "solarized_light": THEME_SOLARIZED_LIGHT,
    "midnight": THEME_MIDNIGHT,
    "emerald": THEME_EMERALD,
    "violet": THEME_VIOLET,
    "nord": THEME_NORD,
    "dracula": THEME_DRACULA,
    "amber": THEME_AMBER,
    "cyber": THEME_CYBER,
}


# ---------------------------------------------------------------------------
# Stylesheet Generators
# ---------------------------------------------------------------------------

def _gen_dark_theme(p: ThemePalette) -> str:
    return f"""
QMainWindow, QDialog {{
    background-color: {p.bg_base};
}}

QWidget#centralWidget {{
    background-color: {p.bg_base};
}}

QLabel {{
    color: {p.text_primary};
    font-size: 12px;
}}

QPushButton {{
    background-color: {p.bg_elevated};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {p.bg_hover};
    border-color: {p.accent};
}}

QPushButton:pressed {{
    background-color: {p.bg_pressed};
    border-color: {p.accent};
}}

QTabBar::tab {{
    background-color: {p.bg_elevated};
    color: {p.text_dim};
    border: 1px solid {p.border};
    border-bottom: none;
    padding: 6px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 12px;
}}

QTabBar::tab:selected {{
    background-color: {p.bg_base};
    color: {p.accent};
    border-color: {p.border_light};
}}

QTabBar::tab:hover:!selected {{
    background-color: {p.bg_pressed};
    color: {p.text_primary};
}}

QMenu {{
    background-color: {p.bg_input};
    color: {p.text_primary};
    border: 1px solid {p.border};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {p.bg_hover};
}}

QMenu::separator {{
    height: 1px;
    background-color: {p.border};
    margin: 4px 8px;
}}

QLineEdit, QSpinBox, QComboBox {{
    background-color: {p.bg_input};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {p.accent};
}}

QCheckBox {{
    color: {p.text_primary};
    font-size: 12px;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {p.border};
    background-color: {p.bg_input};
}}

QCheckBox::indicator:checked {{
    background-color: {p.accent};
    border-color: {p.accent};
}}

QGroupBox {{
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-size: 12px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}}

QScrollBar:vertical {{
    background-color: {p.bg_base};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {p.border};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {p.scrollbar_handle_hover};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QListWidget {{
    background-color: {p.bg_input};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: 4px;
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 4px 8px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {p.bg_hover};
    color: {p.accent};
}}

QDialogButtonBox QPushButton {{
    min-width: 80px;
    padding: 6px 16px;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {p.border};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {p.accent};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}

QSlider::handle:horizontal:hover {{
    background: {p.accent_hover};
}}

QSlider::sub-page:horizontal {{
    background: {p.accent};
    border-radius: 2px;
}}

QSplitter::handle {{
    background-color: {p.border_dark};
    width: 2px;
}}

QSplitter::handle:hover {{
    background-color: {p.border_light};
}}

QTextEdit {{
    background-color: {p.bg_input};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: 4px;
    padding: 4px;
    font-size: 12px;
}}

QTextEdit:focus {{
    border-color: {p.accent};
}}
"""


def _gen_deck_button_style(p: ThemePalette) -> str:
    return f"""
QPushButton#deckButton {{
    background-color: {p.bg_button};
    color: {p.text_white};
    border: 2px solid {p.border_dark};
    border-radius: 10px;
    font-size: 10px;
    padding: 4px;
}}

QPushButton#deckButton:hover {{
    background-color: {p.bg_pressed};
    border-color: {p.accent};
    color: {p.text_bright};
}}

QPushButton#deckButton:pressed {{
    background-color: {p.bg_elevated};
    border-color: {p.accent};
}}
"""


def _gen_deck_button_empty_style(p: ThemePalette) -> str:
    return f"""
QPushButton#deckButton {{
    background-color: {p.bg_titlebar};
    color: {p.text_muted};
    border: 1px dashed {p.border_dark};
    border-radius: 10px;
    font-size: 10px;
    padding: 4px;
}}

QPushButton#deckButton:hover {{
    background-color: {p.bg_base};
    border-color: {p.border};
    color: {p.text_empty_hover};
}}
"""


def _gen_monitor_button_style(p: ThemePalette) -> str:
    return f"""
QPushButton#deckButton {{
    background-color: {p.bg_button};
    color: {p.monitor_green};
    border: 2px solid {p.border_dark};
    border-radius: 10px;
    font-size: 10px;
    padding: 4px;
}}
"""


def _gen_folder_tree_style(p: ThemePalette) -> str:
    return f"""
QTreeWidget#folderTree {{
    background-color: {p.bg_button};
    color: {p.text_primary};
    border: none;
    border-right: 1px solid {p.border_dark};
    outline: none;
    font-size: 12px;
}}

QTreeWidget#folderTree::item {{
    padding: 4px 8px;
    border-radius: 0px;
}}

QTreeWidget#folderTree::item:selected {{
    background-color: {p.bg_pressed};
    color: {p.accent};
}}

QTreeWidget#folderTree::item:hover:!selected {{
    background-color: {p.bg_input};
}}

QTreeWidget#folderTree::branch {{
    background-color: {p.bg_button};
}}

QTreeWidget#folderTree::branch:has-children:!has-siblings:closed,
QTreeWidget#folderTree::branch:closed:has-children:has-siblings {{
    image: none;
    border-image: none;
}}

QTreeWidget#folderTree::branch:open:has-children:!has-siblings,
QTreeWidget#folderTree::branch:open:has-children:has-siblings {{
    image: none;
    border-image: none;
}}

QHeaderView::section {{
    background-color: {p.bg_button};
    color: {p.accent};
    border: none;
    border-bottom: 1px solid {p.border_dark};
    padding: 4px 8px;
    font-size: 11px;
    font-weight: bold;
}}
"""


def _gen_title_bar_style(p: ThemePalette) -> str:
    return f"""
QWidget#titleBar {{
    background-color: {p.bg_titlebar};
    border-bottom: 1px solid {p.border_dark};
    padding: 5px;
}}
"""


# ---------------------------------------------------------------------------
# Theme Resolution
# ---------------------------------------------------------------------------

_theme_cache: dict[str, ThemeStylesheets] = {}


def get_theme(name: str) -> ThemeStylesheets:
    """Get pre-generated stylesheets for a theme. Falls back to dark."""
    if name in _theme_cache:
        return _theme_cache[name]

    palette = THEMES.get(name, THEME_DARK)
    theme = ThemeStylesheets(
        palette=palette,
        dark_theme=_gen_dark_theme(palette),
        deck_button_style=_gen_deck_button_style(palette),
        deck_button_empty_style=_gen_deck_button_empty_style(palette),
        monitor_button_style=_gen_monitor_button_style(palette),
        folder_tree_style=_gen_folder_tree_style(palette),
        title_bar_style=_gen_title_bar_style(palette),
    )
    _theme_cache[name] = theme
    return theme


# ---------------------------------------------------------------------------
# Backward Compatibility — module-level constants for existing imports
# ---------------------------------------------------------------------------

_default = get_theme("dark")
DARK_THEME = _default.dark_theme
DECK_BUTTON_STYLE = _default.deck_button_style
DECK_BUTTON_EMPTY_STYLE = _default.deck_button_empty_style
MONITOR_BUTTON_STYLE = _default.monitor_button_style
FOLDER_TREE_STYLE = _default.folder_tree_style
TITLE_BAR_STYLE = _default.title_bar_style
