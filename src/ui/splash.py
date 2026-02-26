from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QFont, QLinearGradient, QRadialGradient,
)
from PyQt6.QtWidgets import QSplashScreen, QApplication

from ..version import APP_VERSION

if TYPE_CHECKING:
    from .styles import ThemePalette


class Splash(QSplashScreen):
    """Minimal startup splash with fade-in/out and animated loading dots."""

    _WIDTH = 340
    _HEIGHT = 170
    _FADE_IN_MS = 300
    _STAY_MS = 1500
    _FADE_OUT_MS = 400
    _DOT_INTERVAL_MS = 400

    def __init__(self, palette: ThemePalette | None = None) -> None:
        super().__init__()
        self._palette = palette
        self._dot_count = 0
        self.setFixedSize(self._WIDTH, self._HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)
        self._center_on_screen()

        # Dot animation timer
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._tick_dots)

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self._WIDTH) // 2
            y = geo.y() + (geo.height() - self._HEIGHT) // 2
            self.move(x, y)

    def show_and_close(self) -> None:
        self.show()
        self._dot_timer.start(self._DOT_INTERVAL_MS)

        # Fade in
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(self._FADE_IN_MS)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.start()

        # Schedule fade out
        QTimer.singleShot(self._FADE_IN_MS + self._STAY_MS, self._fade_out)

    def _fade_out(self) -> None:
        self._dot_timer.stop()
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(self._FADE_OUT_MS)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_anim.finished.connect(self.close)
        self._fade_anim.start()

    def _tick_dots(self) -> None:
        self._dot_count = (self._dot_count + 1) % 4
        self.update()

    def paintEvent(self, event) -> None:
        pal = self._palette

        bg_color = pal.splash_bg if pal else "#0a0a0a"
        accent = pal.accent if pal else "#e94560"
        gradient_end = pal.splash_gradient_end if pal else "#533483"
        text_dim = pal.text_dim if pal else "#808080"
        text_muted = pal.text_muted if pal else "#303030"
        border_color = pal.border_dark if pal else "#1a1a1a"

        w, h = self._WIDTH, self._HEIGHT
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- Clip to rounded rect for all drawing ---
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, w, h, 14, 14)
        p.setClipPath(clip)

        # --- Background ---
        p.setBrush(QColor(bg_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, 0, w, h)

        # --- Gradient bar at top ---
        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, QColor(accent))
        grad.setColorAt(1.0, QColor(gradient_end))
        p.setBrush(grad)
        p.drawRect(0, 0, w, 3)

        # --- Subtle glow behind title ---
        cx, cy = w // 2, 68
        glow = QRadialGradient(cx, cy, 80)
        accent_color = QColor(accent)
        accent_color.setAlpha(25)
        glow.setColorAt(0.0, accent_color)
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - 80, cy - 40, 160, 80)

        # --- App name ---
        font_title = QFont("Segoe UI", 22)
        font_title.setBold(True)
        font_title.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        p.setFont(font_title)
        p.setPen(QColor(accent))
        title_rect = self.rect().adjusted(0, 28, 0, -60)
        p.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "SteamDeckSoft")

        # --- Version ---
        font_ver = QFont("Segoe UI", 9)
        p.setFont(font_ver)
        p.setPen(QColor(text_dim))
        ver_rect = self.rect().adjusted(0, 68, 0, -40)
        p.drawText(ver_rect, Qt.AlignmentFlag.AlignCenter, f"v{APP_VERSION}")

        # --- Loading dots ---
        font_dots = QFont("Segoe UI", 10)
        p.setFont(font_dots)
        p.setPen(QColor(text_dim))
        dots = "\u00b7" * self._dot_count  # middle dot ·
        dots_text = f"Loading {dots}" if self._dot_count > 0 else "Loading"
        dots_rect = self.rect().adjusted(0, 30, 0, -10)
        p.drawText(dots_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, dots_text)

        # --- Border (draw outside clip so rounded corners are clean) ---
        p.setClipping(False)
        p.setPen(QColor(border_color))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(0, 0, w, h, 14, 14)

        p.end()
