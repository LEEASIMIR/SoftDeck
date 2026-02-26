from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.version import APP_VERSION


@dataclass
class ActionConfig:
    type: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"type": self.type, "params": dict(self.params)}

    @classmethod
    def from_dict(cls, data: dict) -> ActionConfig:
        return cls(
            type=data.get("type", ""),
            params=dict(data.get("params", {})),
        )


@dataclass
class ButtonConfig:
    position: tuple[int, int] = (0, 0)
    label: str = ""
    icon: str = ""
    label_color: str = ""
    label_size: int = 0
    action: ActionConfig = field(default_factory=ActionConfig)

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "position": list(self.position),
            "label": self.label,
            "icon": self.icon,
            "action": self.action.to_dict(),
        }
        if self.label_color:
            d["label_color"] = self.label_color
        if self.label_size:
            d["label_size"] = self.label_size
        return d

    @classmethod
    def from_dict(cls, data: dict) -> ButtonConfig:
        pos = data.get("position", [0, 0])
        return cls(
            position=(pos[0], pos[1]),
            label=data.get("label", ""),
            icon=data.get("icon", ""),
            label_color=data.get("label_color", ""),
            label_size=data.get("label_size", 0),
            action=ActionConfig.from_dict(data.get("action", {})),
        )


@dataclass
class FolderConfig:
    id: str = ""
    name: str = "New Folder"
    mapped_apps: list[str] = field(default_factory=list)
    buttons: list[ButtonConfig] = field(default_factory=list)
    children: list[FolderConfig] = field(default_factory=list)
    expanded: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "mapped_apps": list(self.mapped_apps),
            "buttons": [b.to_dict() for b in self.buttons],
            "children": [c.to_dict() for c in self.children],
            "expanded": self.expanded,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FolderConfig:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "New Folder"),
            mapped_apps=list(data.get("mapped_apps", [])),
            buttons=[ButtonConfig.from_dict(b) for b in data.get("buttons", [])],
            children=[FolderConfig.from_dict(c) for c in data.get("children", [])],
            expanded=data.get("expanded", True),
        )


# Kept for v1 migration only (deprecated)
@dataclass
class PageConfig:
    id: str = ""
    name: str = "New Page"
    mapped_apps: list[str] = field(default_factory=list)
    buttons: list[ButtonConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> PageConfig:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "New Page"),
            mapped_apps=list(data.get("mapped_apps", [])),
            buttons=[ButtonConfig.from_dict(b) for b in data.get("buttons", [])],
        )


@dataclass
class AppSettings:
    grid_rows: int = 3
    grid_cols: int = 5
    button_size: int = 60
    button_spacing: int = 8
    default_label_size: int = 10
    auto_switch_enabled: bool = True
    always_on_top: bool = True
    theme: str = "dark"
    global_hotkey: str = "ctrl+`"
    window_opacity: float = 1.0
    folder_tree_visible: bool = True
    window_x: int | None = None
    window_y: int | None = None
    default_label_family: str = ""

    def to_dict(self) -> dict:
        return {
            "grid_rows": self.grid_rows,
            "grid_cols": self.grid_cols,
            "button_size": self.button_size,
            "button_spacing": self.button_spacing,
            "default_label_size": self.default_label_size,
            "default_label_family": self.default_label_family,
            "auto_switch_enabled": self.auto_switch_enabled,
            "always_on_top": self.always_on_top,
            "theme": self.theme,
            "global_hotkey": self.global_hotkey,
            "window_opacity": self.window_opacity,
            "folder_tree_visible": self.folder_tree_visible,
            "window_x": self.window_x,
            "window_y": self.window_y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppSettings:
        return cls(
            grid_rows=data.get("grid_rows", 3),
            grid_cols=data.get("grid_cols", 5),
            button_size=data.get("button_size", 60),
            button_spacing=data.get("button_spacing", 8),
            default_label_size=data.get("default_label_size", 10),
            default_label_family=data.get("default_label_family", ""),
            auto_switch_enabled=data.get("auto_switch_enabled", True),
            always_on_top=data.get("always_on_top", True),
            theme=data.get("theme", "dark"),
            global_hotkey=data.get("global_hotkey", "ctrl+`"),
            window_opacity=max(0.2, min(1.0, data.get("window_opacity", 0.9))),
            folder_tree_visible=data.get("folder_tree_visible", True),
            window_x=data.get("window_x"),
            window_y=data.get("window_y"),
        )


@dataclass
class AppConfig:
    version: int = 2
    app_version: str = APP_VERSION
    settings: AppSettings = field(default_factory=AppSettings)
    root_folder: FolderConfig = field(default_factory=lambda: FolderConfig(id="root", name="Root"))

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "app_version": APP_VERSION,
            "settings": self.settings.to_dict(),
            "root_folder": self.root_folder.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppConfig:
        version = data.get("version", 1)
        settings = AppSettings.from_dict(data.get("settings", {}))

        if version < 2:
            root_folder = _migrate_v1(data)
        else:
            root_folder = FolderConfig.from_dict(data.get("root_folder", {"id": "root", "name": "Root"}))

        return cls(
            version=2,
            app_version=APP_VERSION,
            settings=settings,
            root_folder=root_folder,
        )


def _migrate_v1(data: dict) -> FolderConfig:
    """Convert v1 pages list into v2 root_folder tree."""
    pages_data = data.get("pages", [])
    children: list[FolderConfig] = []
    for p_data in pages_data:
        page = PageConfig.from_dict(p_data)
        children.append(FolderConfig(
            id=page.id,
            name=page.name,
            mapped_apps=page.mapped_apps,
            buttons=page.buttons,
            children=[],
            expanded=True,
        ))

    root = FolderConfig(
        id="root",
        name="Root",
        mapped_apps=[],
        buttons=[],
        children=children,
        expanded=True,
    )

    # If there's only one child, hoist its buttons to root for cleaner UX
    if len(children) == 1:
        only = children[0]
        root.buttons = only.buttons
        root.mapped_apps = only.mapped_apps
        root.children = []

    return root
