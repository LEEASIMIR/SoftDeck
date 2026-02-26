from __future__ import annotations

import logging
import os
import subprocess
from typing import Any

from .base import ActionBase

logger = logging.getLogger(__name__)


class LaunchAppAction(ActionBase):
    def execute(self, params: dict[str, Any]) -> None:
        path = params.get("path", "")
        args = params.get("args", "")
        working_dir = params.get("working_dir", "")

        if not path:
            logger.warning("launch_app: no path specified")
            return

        try:
            if not args:
                os.startfile(path)
                logger.info("Launched via startfile: %s", path)
            else:
                cmd = [path] + args.split()
                kwargs: dict[str, Any] = {
                    "creationflags": subprocess.CREATE_NEW_CONSOLE,
                }
                if working_dir and os.path.isdir(working_dir):
                    kwargs["cwd"] = working_dir
                subprocess.Popen(cmd, **kwargs)
                logger.info("Launched: %s %s", path, args)
        except Exception:
            logger.exception("Failed to launch app: %s", path)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
