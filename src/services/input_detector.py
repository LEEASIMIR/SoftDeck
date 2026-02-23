from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import threading

logger = logging.getLogger(__name__)

LLKHF_INJECTED = 0x00000010
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

user32 = ctypes.windll.user32

# Set correct arg/res types for CallNextHookEx (64-bit safe)
user32.CallNextHookEx.argtypes = [
    ctypes.wintypes.HHOOK,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
]
user32.CallNextHookEx.restype = ctypes.wintypes.LPARAM

# HOOKPROC: must use LPARAM (pointer-sized) for return and lParam
HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.wintypes.LPARAM,  # return
    ctypes.c_int,            # nCode
    ctypes.wintypes.WPARAM,  # wParam
    ctypes.wintypes.LPARAM,  # lParam
)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class InputDetector:
    """Tracks whether the most recent key event was injected (software-generated)."""

    def __init__(self) -> None:
        self._last_injected = False
        self._hook = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._proc = HOOKPROC(self._hook_proc)

    @property
    def last_was_injected(self) -> bool:
        return self._last_injected

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            thread_id = self._thread.ident
            if thread_id:
                user32.PostThreadMessageW(thread_id, 0x0012, 0, 0)
            self._thread.join(timeout=2)

    def _hook_proc(self, nCode, wParam, lParam):
        if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            self._last_injected = bool(kb.flags & LLKHF_INJECTED)
        return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

    def _run(self) -> None:
        self._hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._proc, None, 0
        )
        if not self._hook:
            logger.error("Failed to install keyboard hook")
            return
        logger.info("InputDetector hook installed")

        msg = ctypes.wintypes.MSG()
        while self._running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnhookWindowsHookEx(self._hook)
        self._hook = None
        logger.info("InputDetector hook removed")
