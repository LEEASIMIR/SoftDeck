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
            cmd = [path]
            if args:
                cmd.extend(args.split())

            kwargs: dict[str, Any] = {
                "creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            }
            if working_dir and os.path.isdir(working_dir):
                kwargs["cwd"] = working_dir

            subprocess.Popen(cmd, **kwargs)
            logger.info("Launched: %s", path)
        except FileNotFoundError:
            # Try with shell for system apps like calc.exe
            try:
                os.startfile(path)
                logger.info("Launched via startfile: %s", path)
            except Exception:
                logger.exception("Failed to launch app: %s", path)
        except Exception:
            logger.exception("Failed to launch app: %s", path)

    def get_display_text(self, params: dict[str, Any]) -> str | None:
        return None
