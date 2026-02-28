from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRectF,
    QTimer,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from .styles import ThemePalette


class ToastType(IntEnum):
    INFO = 0
    SUCCESS = 1
    WARNING = 2
    ERROR = 3


_TYPE_COLORS: dict[ToastType, str | None] = {
    ToastType.INFO: None,  # uses theme accent
    ToastType.SUCCESS: "#4caf50",
    ToastType.WARNING: "#ff9800",
    ToastType.ERROR: "#f44336",
}


class _ToastWidget(QWidget):
    """Single toast notification with themed styling and smooth animation."""

    closed = pyqtSignal(object)

    _WIDTH = 300
    _ACCENT_W = 4
    _PROGRESS_H = 3
    _RADIUS = 10
    _EDGE = 2  # outer margin for anti-aliased edges

    def __init__(
        self,
        palette: ThemePalette,
        toast_type: ToastType,
        title: str,
        message: str,
        duration_ms: int,
    ) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._palette = palette
        self._duration_ms = duration_ms
        self._progress_value = 1.0
        self._dismissing = False

        color = _TYPE_COLORS.get(toast_type)
        self._accent = QColor(color if color else palette.accent)

        self._build_ui(title, message)
        self.setFixedWidth(self._WIDTH)

    # ---- layout --------------------------------------------------------

    def _build_ui(self, title: str, message: str) -> None:
        pad = 14
        e = self._EDGE
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            e + self._ACCENT_W + pad,
            e + pad,
            e + pad,
            e + pad + self._PROGRESS_H,
        )
        layout.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(
            f"color: {self._palette.text_bright}; font-size: 13px; "
            f"font-weight: bold; background: transparent;"
        )
        layout.addWidget(t)

        if message:
            m = QLabel(message)
            m.setWordWrap(True)
            m.setStyleSheet(
                f"color: {self._palette.text_primary}; font-size: 12px; "
                f"background: transparent;"
            )
            layout.addWidget(m)

    # ---- paint ---------------------------------------------------------

    def paintEvent(self, _event: object) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        e = self._EDGE
        rect = QRectF(e, e, self.width() - 2 * e, self.height() - 2 * e)

        # background
        bg_path = QPainterPath()
        bg_path.addRoundedRect(rect, self._RADIUS, self._RADIUS)
        bg = QColor(self._palette.bg_elevated)
        bg.setAlpha(245)
        p.fillPath(bg_path, bg)

        # border
        p.setPen(QPen(QColor(self._palette.border_light), 1))
        p.drawPath(bg_path)

        # accent bar (left, between rounded corners)
        bar = QRectF(
            rect.x() + 1,
            rect.y() + self._RADIUS,
            self._ACCENT_W,
            rect.height() - 2 * self._RADIUS,
        )
        bar_path = QPainterPath()
        bar_path.addRoundedRect(bar, 2, 2)
        p.fillPath(bar_path, self._accent)

        # progress bar (bottom)
        if self._progress_value > 0.001:
            avail_w = rect.width() - 2 * self._RADIUS
            pr = QRectF(
                rect.x() + self._RADIUS,
                rect.bottom() - self._PROGRESS_H - 2,
                avail_w * self._progress_value,
                self._PROGRESS_H,
            )
            pp = QPainterPath()
            pp.addRoundedRect(pr, 1.5, 1.5)
            pc = QColor(self._accent)
            pc.setAlpha(100)
            p.fillPath(pp, pc)

        p.end()

    # ---- animation -----------------------------------------------------

    def show_animated(self, target: QPoint) -> None:
        start = QPoint(target.x(), target.y() + 20)
        self.move(start)
        self.setWindowOpacity(0.0)
        self.show()

        slide = QPropertyAnimation(self, b"pos", self)
        slide.setStartValue(start)
        slide.setEndValue(target)
        slide.setDuration(300)
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)

        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setDuration(300)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._show_group = QParallelAnimationGroup(self)
        self._show_group.addAnimation(slide)
        self._show_group.addAnimation(fade)
        self._show_group.start()

        # progress shrink
        self._prog_anim = QPropertyAnimation(self, b"progress", self)
        self._prog_anim.setStartValue(1.0)
        self._prog_anim.setEndValue(0.0)
        self._prog_anim.setDuration(self._duration_ms)
        self._prog_anim.start()

        # auto-dismiss
        QTimer.singleShot(self._duration_ms, self._dismiss)

    def _dismiss(self) -> None:
        if self._dismissing or not self.isVisible():
            return
        self._dismissing = True

        out = QPropertyAnimation(self, b"windowOpacity", self)
        out.setStartValue(self.windowOpacity())
        out.setEndValue(0.0)
        out.setDuration(250)
        out.setEasingCurve(QEasingCurve.Type.InCubic)
        out.finished.connect(self._on_dismissed)
        self._fade_out = out
        out.start()

    def _on_dismissed(self) -> None:
        self.closed.emit(self)
        self.close()

    def mousePressEvent(self, _event: object) -> None:
        self._dismiss()

    # ---- progress property ---------------------------------------------

    @pyqtProperty(float)
    def progress(self) -> float:
        return self._progress_value

    @progress.setter  # type: ignore[attr-defined]
    def progress(self, v: float) -> None:
        self._progress_value = v
        self.update()


class ToastManager:
    """Shows themed toast notifications stacked at the bottom-right."""

    _SCREEN_MARGIN = 16
    _SPACING = 8

    def __init__(self, palette: ThemePalette) -> None:
        self._palette = palette
        self._active: list[_ToastWidget] = []

    def set_palette(self, palette: ThemePalette) -> None:
        self._palette = palette

    def show(
        self,
        title: str,
        message: str = "",
        toast_type: ToastType = ToastType.INFO,
        duration_ms: int = 3000,
    ) -> None:
        toast = _ToastWidget(
            self._palette, toast_type, title, message, duration_ms,
        )
        toast.adjustSize()
        toast.closed.connect(self._on_closed)

        screen = QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()

        x = avail.right() - toast.width() - self._SCREEN_MARGIN
        y = avail.bottom() - toast.height() - self._SCREEN_MARGIN

        for t in self._active:
            y -= t.height() + self._SPACING

        self._active.append(toast)
        toast.show_animated(QPoint(x, y))

    def _on_closed(self, toast: _ToastWidget) -> None:
        if toast in self._active:
            self._active.remove(toast)
        self._reposition()

    def _reposition(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()

        y = avail.bottom() - self._SCREEN_MARGIN
        for toast in self._active:
            y -= toast.height()
            x = avail.right() - toast.width() - self._SCREEN_MARGIN
            anim = QPropertyAnimation(toast, b"pos", toast)
            anim.setEndValue(QPoint(x, y))
            anim.setDuration(200)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            toast._repos_anim = anim  # prevent GC
            anim.start()
            y -= self._SPACING
