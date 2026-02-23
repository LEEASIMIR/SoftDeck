from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    action: ActionConfig = field(default_factory=ActionConfig)

    def to_dict(self) -> dict:
        return {
            "position": list(self.position),
            "label": self.label,
            "icon": self.icon,
            "action": self.action.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ButtonConfig:
        pos = data.get("position", [0, 0])
        return cls(
            position=(pos[0], pos[1]),
            label=data.get("label", ""),
            icon=data.get("icon", ""),
            action=ActionConfig.from_dict(data.get("action", {})),
        )


@dataclass
class PageConfig:
    id: str = ""
    name: str = "New Page"
    mapped_apps: list[str] = field(default_factory=list)
    buttons: list[ButtonConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "mapped_apps": list(self.mapped_apps),
            "buttons": [b.to_dict() for b in self.buttons],
        }

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
    button_size: int = 100
    button_spacing: int = 8
    auto_switch_enabled: bool = True
    always_on_top: bool = True
    theme: str = "dark"
    global_hotkey: str = "ctrl+`"

    def to_dict(self) -> dict:
        return {
            "grid_rows": self.grid_rows,
            "grid_cols": self.grid_cols,
            "button_size": self.button_size,
            "button_spacing": self.button_spacing,
            "auto_switch_enabled": self.auto_switch_enabled,
            "always_on_top": self.always_on_top,
            "theme": self.theme,
            "global_hotkey": self.global_hotkey,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppSettings:
        return cls(
            grid_rows=data.get("grid_rows", 3),
            grid_cols=data.get("grid_cols", 5),
            button_size=data.get("button_size", 100),
            button_spacing=data.get("button_spacing", 8),
            auto_switch_enabled=data.get("auto_switch_enabled", True),
            always_on_top=data.get("always_on_top", True),
            theme=data.get("theme", "dark"),
            global_hotkey=data.get("global_hotkey", "ctrl+`"),
        )


@dataclass
class AppConfig:
    version: int = 1
    settings: AppSettings = field(default_factory=AppSettings)
    pages: list[PageConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "settings": self.settings.to_dict(),
            "pages": [p.to_dict() for p in self.pages],
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppConfig:
        return cls(
            version=data.get("version", 1),
            settings=AppSettings.from_dict(data.get("settings", {})),
            pages=[PageConfig.from_dict(p) for p in data.get("pages", [])],
        )
