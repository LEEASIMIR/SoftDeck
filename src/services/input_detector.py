from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import threading

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

LLKHF_INJECTED = 0x00000010
LLKHF_EXTENDED = 0x00000001
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
VK_NUMLOCK = 0x90

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


class _NumpadSignal(QObject):
    """Bridge to emit numpad presses from the hook thread to the Qt main thread."""
    pressed = pyqtSignal(int, int)
    numlock_changed = pyqtSignal(bool)  # True = Num Lock ON, False = OFF


class InputDetector:
    """Tracks injected keys and provides global numpad shortcuts (Num Lock OFF only)."""

    # When Num Lock is OFF, numpad keys send navigation VK codes WITHOUT the extended flag.
    # Regular arrow/Home/End keys send the SAME VK codes but WITH the extended flag.
    _NUMPAD_MAP: dict[int, tuple[int, int]] = {
        0x24: (0, 0),  # VK_HOME   → numpad 7
        0x26: (0, 1),  # VK_UP     → numpad 8
        0x21: (0, 2),  # VK_PRIOR  → numpad 9
        0x25: (1, 0),  # VK_LEFT   → numpad 4
        0x0C: (1, 1),  # VK_CLEAR  → numpad 5
        0x27: (1, 2),  # VK_RIGHT  → numpad 6
        0x23: (2, 0),  # VK_END    → numpad 1
        0x28: (2, 1),  # VK_DOWN   → numpad 2
        0x22: (2, 2),  # VK_NEXT   → numpad 3
    }

    def __init__(self) -> None:
        self._last_injected = False
        self._hook = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._proc = HOOKPROC(self._hook_proc)
        self.numpad_signal = _NumpadSignal()

    @property
    def last_was_injected(self) -> bool:
        return self._last_injected

    @staticmethod
    def is_numlock_on() -> bool:
        """Return True if Num Lock is currently active."""
        return bool(user32.GetKeyState(VK_NUMLOCK) & 1)

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

    def _is_numpad_nav_key(self, kb: KBDLLHOOKSTRUCT) -> tuple[int, int] | None:
        """Check if key is a numpad navigation key (Num Lock OFF, non-extended, non-injected)."""
        if kb.flags & LLKHF_INJECTED:
            return None
        if kb.flags & LLKHF_EXTENDED:
            return None
        if user32.GetKeyState(VK_NUMLOCK) & 1:
            return None
        return self._NUMPAD_MAP.get(kb.vkCode)

    def _hook_proc(self, nCode, wParam, lParam):
        if nCode >= 0:
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                self._last_injected = bool(kb.flags & LLKHF_INJECTED)

                # Detect Num Lock toggle
                if kb.vkCode == VK_NUMLOCK:
                    # Hook fires before state flips, so invert current state
                    will_be_on = not bool(user32.GetKeyState(VK_NUMLOCK) & 1)
                    self.numpad_signal.numlock_changed.emit(will_be_on)

                pos = self._is_numpad_nav_key(kb)
                if pos is not None:
                    self.numpad_signal.pressed.emit(pos[0], pos[1])
                    return 1  # suppress

            elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                # Suppress matching key-up to avoid orphan events
                if self._is_numpad_nav_key(kb) is not None:
                    return 1

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
