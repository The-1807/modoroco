"""Purpose-built Qt widgets for the focus experience."""

from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .theme import BORDER, INK, MUTED, RED


class TimerDial(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(330, 330)
        self._progress = 1.0
        self._time = "25:00"
        self._caption = "READY TO FOCUS"
        self.animation = QPropertyAnimation(self, b"progress", self)
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def get_progress(self) -> float:
        return self._progress

    def set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, value))
        self.update()

    progress = Property(float, get_progress, set_progress)

    def display(self, time_text: str, caption: str, progress: float) -> None:
        self._time = time_text
        self._caption = caption
        self.animation.stop()
        self.animation.setStartValue(self._progress)
        self.animation.setEndValue(progress)
        self.animation.start()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 34
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        painter.setPen(QPen(QColor(BORDER), 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 0, 360 * 16)
        painter.setPen(QPen(QColor(RED), 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 90 * 16, -int(360 * 16 * self._progress))
        painter.setPen(QColor(INK))
        font = QFont("Segoe UI Variable", 50, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 98)
        painter.setFont(font)
        painter.drawText(rect.adjusted(0, -13, 0, 0), Qt.AlignmentFlag.AlignCenter, self._time)
        painter.setPen(QColor(MUTED))
        painter.setFont(QFont("Segoe UI Variable", 9, QFont.Weight.DemiBold))
        painter.drawText(rect.adjusted(0, 75, 0, 0), Qt.AlignmentFlag.AlignCenter, self._caption)


class MetricCard(QFrame):
    def __init__(self, value: str, label: str, accent: str = RED) -> None:
        super().__init__()
        self.setObjectName("card")
        self.setMinimumHeight(105)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        marker = QLabel("●")
        marker.setStyleSheet(f"color: {accent}; font-size: 9px;")
        number = QLabel(value)
        number.setObjectName("metric")
        caption = QLabel(label.upper())
        caption.setObjectName("metricLabel")
        layout.addWidget(marker)
        layout.addWidget(number)
        layout.addWidget(caption)


class SessionRow(QFrame):
    def __init__(self, title: str, detail: str, duration: str, active: bool = False) -> None:
        super().__init__()
        self.setObjectName("sessionCard" if active else "card")
        self.setMinimumHeight(78)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 13, 18, 13)
        top = QLabel(title)
        top.setStyleSheet("font-size: 14px; font-weight: 650;")
        bottom = QLabel(f"{detail}   •   {duration}")
        bottom.setObjectName("subtle")
        if active:
            bottom.setStyleSheet("color: #b9bec7; font-size: 12px;")
        layout.addWidget(top)
        layout.addWidget(bottom)
