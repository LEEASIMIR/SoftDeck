from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

from .models import AppConfig

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
    def pages(self):
        return self._config.pages

    def load(self) -> AppConfig:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._config = AppConfig.from_dict(data)
                logger.info("Loaded user config from %s", self._path)
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

    def get_page_by_id(self, page_id: str):
        for page in self._config.pages:
            if page.id == page_id:
                return page
        return None

    def find_page_for_app(self, exe_name: str):
        exe_lower = exe_name.lower()
        for page in self._config.pages:
            for app in page.mapped_apps:
                if app.lower() == exe_lower:
                    return page
        return None
