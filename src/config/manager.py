from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
from pathlib import Path

from .models import AppConfig, FolderConfig

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "default_config.json"
_USER_CONFIG_DIR = Path(os.environ.get("APPDATA", "~")) / "SteamDeckSoft"
_USER_CONFIG_PATH = _USER_CONFIG_DIR / "config.json"


class ConfigManager:
    def __init__(self) -> None:
        self._config: AppConfig = AppConfig()
        self._path = _USER_CONFIG_PATH

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def settings(self):
        return self._config.settings

    @property
    def root_folder(self) -> FolderConfig:
        return self._config.root_folder

    def load(self) -> AppConfig:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                old_version = data.get("version", 1)
                self._config = AppConfig.from_dict(data)
                logger.info("Loaded user config from %s", self._path)
                # Re-save if migrated from v1
                if old_version < 2:
                    logger.info("Migrated config from v%d to v2", old_version)
                    self.save()
                return self._config
            except Exception:
                logger.exception("Failed to load user config, falling back to default")

        if _DEFAULT_CONFIG_PATH.exists():
            try:
                data = json.loads(_DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
                self._config = AppConfig.from_dict(data)
                logger.info("Loaded default config")
            except Exception:
                logger.exception("Failed to load default config, using built-in defaults")
                self._config = AppConfig()
        else:
            self._config = AppConfig()

        self.save()
        return self._config

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = self._path.with_suffix(".tmp")
        try:
            tmp_path.write_text(
                json.dumps(self._config.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            shutil.move(str(tmp_path), str(self._path))
            logger.info("Config saved to %s", self._path)
        except Exception:
            logger.exception("Failed to save config")
            if tmp_path.exists():
                tmp_path.unlink()

    # --- Folder operations ---

    def get_folder_by_id(self, folder_id: str) -> FolderConfig | None:
        """DFS search for a folder by id."""
        return self._find_folder(self._config.root_folder, folder_id)

    def _find_folder(self, folder: FolderConfig, folder_id: str) -> FolderConfig | None:
        if folder.id == folder_id:
            return folder
        for child in folder.children:
            result = self._find_folder(child, folder_id)
            if result is not None:
                return result
        return None

    def find_parent_folder(self, folder_id: str) -> FolderConfig | None:
        """Find the parent of a folder by id."""
        return self._find_parent(self._config.root_folder, folder_id)

    def _find_parent(self, folder: FolderConfig, folder_id: str) -> FolderConfig | None:
        for child in folder.children:
            if child.id == folder_id:
                return folder
            result = self._find_parent(child, folder_id)
            if result is not None:
                return result
        return None

    def find_folder_for_app(self, exe_name: str) -> FolderConfig | None:
        """DFS search for a folder mapped to the given app."""
        exe_lower = exe_name.lower()
        return self._find_folder_for_app(self._config.root_folder, exe_lower)

    def _find_folder_for_app(self, folder: FolderConfig, exe_lower: str) -> FolderConfig | None:
        for app in folder.mapped_apps:
            if app.lower() == exe_lower:
                return folder
        for child in folder.children:
            result = self._find_folder_for_app(child, exe_lower)
            if result is not None:
                return result
        return None

    def add_folder(self, parent_id: str, name: str = "New Folder") -> FolderConfig | None:
        """Create a new sub-folder under parent_id. Returns the new folder or None."""
        parent = self.get_folder_by_id(parent_id)
        if parent is None:
            return None
        new_folder = FolderConfig(
            id=f"folder_{uuid.uuid4().hex[:8]}",
            name=name,
        )
        parent.children.append(new_folder)
        self.save()
        return new_folder

    def rename_folder(self, folder_id: str, new_name: str) -> bool:
        if folder_id == "root":
            return False
        folder = self.get_folder_by_id(folder_id)
        if folder is None:
            return False
        folder.name = new_name
        self.save()
        return True

    def delete_folder(self, folder_id: str) -> bool:
        if folder_id == "root":
            return False
        parent = self.find_parent_folder(folder_id)
        if parent is None:
            return False
        parent.children = [c for c in parent.children if c.id != folder_id]
        self.save()
        return True

    def move_folder(self, folder_id: str, new_parent_id: str, position: int = -1) -> bool:
        """Move a folder to new_parent_id at position. Returns False on cycle or invalid."""
        if folder_id == "root":
            return False
        folder = self.get_folder_by_id(folder_id)
        if folder is None:
            return False
        new_parent = self.get_folder_by_id(new_parent_id)
        if new_parent is None:
            return False

        # Cycle check: new_parent must not be a descendant of folder
        if self._is_descendant(folder, new_parent_id):
            return False

        # Remove from old parent
        old_parent = self.find_parent_folder(folder_id)
        if old_parent is None:
            return False
        old_parent.children = [c for c in old_parent.children if c.id != folder_id]

        # Insert into new parent
        if position < 0 or position >= len(new_parent.children):
            new_parent.children.append(folder)
        else:
            new_parent.children.insert(position, folder)

        self.save()
        return True

    def _is_descendant(self, ancestor: FolderConfig, target_id: str) -> bool:
        """Check if target_id is ancestor itself or a descendant of ancestor."""
        if ancestor.id == target_id:
            return True
        for child in ancestor.children:
            if self._is_descendant(child, target_id):
                return True
        return False

    def export_config(self, path: Path) -> None:
        """Export current config to a JSON file."""
        path.write_text(
            json.dumps(self._config.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Config exported to %s", path)

    def import_config(self, path: Path) -> None:
        """Import config from a JSON file, replacing the current config."""
        data = json.loads(path.read_text(encoding="utf-8"))
        self._config = AppConfig.from_dict(data)
        self.save()
        logger.info("Config imported from %s", path)

    def get_all_folders_flat(self) -> list[tuple[FolderConfig, int]]:
        """Return flat list of (folder, depth) for combo boxes."""
        result: list[tuple[FolderConfig, int]] = []
        self._collect_folders(self._config.root_folder, 0, result)
        return result

    def _collect_folders(self, folder: FolderConfig, depth: int, result: list[tuple[FolderConfig, int]]) -> None:
        result.append((folder, depth))
        for child in folder.children:
            self._collect_folders(child, depth + 1, result)
