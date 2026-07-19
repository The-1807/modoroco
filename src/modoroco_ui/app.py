"""Modoroco's native Qt application shell."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .theme import RED, STYLESHEET
from .timer import TimerSnapshot, TimerState
from .widgets import MetricCard, SessionRow, TimerDial

ASSET_DIR = Path(__file__).resolve().parents[2] / "assets"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ModorocoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("The 1807", "Modoroco")
        self.snapshot = TimerSnapshot.minutes(int(self.settings.value("focus_minutes", 25)))
        self.completed_today = int(self.settings.value("completed_today", 3))
        self._build_window()
        self._build_shortcuts()
        self.ticker = QTimer(self)
        self.ticker.setInterval(250)
        self.ticker.timeout.connect(self._tick)
        self.ticker.start()
        self._render_timer()

    def _build_window(self) -> None:
        self.setWindowTitle("Modoroco — Make time matter")
        self.setMinimumSize(1080, 700)
        self.resize(1260, 790)
        icon_path = ASSET_DIR / "modicon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        root = QWidget(objectName="root")
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        shell.addWidget(self._sidebar())
        self.pages = QStackedWidget()
        self.pages.addWidget(self._focus_page())
        self.pages.addWidget(self._insights_page())
        self.pages.addWidget(self._routines_page())
        self.pages.addWidget(self._settings_page())
        shell.addWidget(self.pages, 1)
        self.setCentralWidget(root)

    def _sidebar(self) -> QWidget:
        side = QFrame(objectName="sidebar")
        side.setFixedWidth(225)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(22, 24, 22, 24)
        layout.setSpacing(7)
        logo = QHBoxLayout()
        mark = QLabel("M")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(38, 38)
        mark.setStyleSheet(
            f"background:{RED}; color:white; border-radius:11px; font-size:20px; font-weight:800;"
        )
        brand = QLabel("MODOROCO", objectName="brand")
        logo.addWidget(mark)
        logo.addWidget(brand)
        logo.addStretch()
        layout.addLayout(logo)
        layout.addSpacing(34)
        self.nav_buttons: list[QPushButton] = []
        for index, (icon, name) in enumerate(
            (("◉", "Focus"), ("↗", "Insights"), ("◇", "Routines"), ("⚙", "Preferences"))
        ):
            button = QPushButton(f"{icon}    {name}", objectName="nav")
            button.setCheckable(True)
            button.setChecked(index == 0)
            button.clicked.connect(lambda checked=False, i=index: self._navigate(i))
            layout.addWidget(button)
            self.nav_buttons.append(button)
        layout.addStretch()
        quote = QLabel("“What you do today can improve all your tomorrows.”")
        quote.setWordWrap(True)
        quote.setObjectName("subtle")
        quote.setStyleSheet("font-style: italic; line-height: 1.4;")
        layout.addWidget(quote)
        layout.addSpacing(14)
        org = QLabel("THE 1807  •  v0.1")
        org.setObjectName("metricLabel")
        layout.addWidget(org)
        return side

    def _focus_page(self) -> QWidget:
        page, content = self._page(
            "YOUR FOCUS SPACE", "Make this hour yours.", "One considered session at a time."
        )
        body = QHBoxLayout()
        body.setSpacing(28)
        timer_card = QFrame(objectName="card")
        timer_layout = QVBoxLayout(timer_card)
        timer_layout.setContentsMargins(28, 22, 28, 25)
        modes = QHBoxLayout()
        for text, minutes in (("Focus", 25), ("Short break", 5), ("Long break", 15)):
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, m=minutes: self._choose_duration(m))
            modes.addWidget(button)
        timer_layout.addLayout(modes)
        self.dial = TimerDial()
        timer_layout.addWidget(self.dial, 1, Qt.AlignmentFlag.AlignCenter)
        controls = QHBoxLayout()
        controls.addStretch()
        self.reset_button = QPushButton("↺", objectName="round")
        self.reset_button.setFixedSize(46, 46)
        self.reset_button.setToolTip("Reset timer")
        self.reset_button.clicked.connect(self._reset)
        self.action_button = QPushButton("Begin focus", objectName="primary")
        self.action_button.setMinimumWidth(150)
        self.action_button.clicked.connect(self._toggle)
        self.skip_button = QPushButton("→", objectName="round")
        self.skip_button.setFixedSize(46, 46)
        self.skip_button.setToolTip("Complete this session")
        self.skip_button.clicked.connect(self._complete)
        controls.addWidget(self.reset_button)
        controls.addSpacing(10)
        controls.addWidget(self.action_button)
        controls.addSpacing(10)
        controls.addWidget(self.skip_button)
        controls.addStretch()
        timer_layout.addLayout(controls)
        self.status_label = QLabel("Space starts the timer  •  R resets")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("subtle")
        timer_layout.addWidget(self.status_label)
        body.addWidget(timer_card, 3)
        right = QVBoxLayout()
        right.setSpacing(16)
        metrics = QHBoxLayout()
        self.today_metric = MetricCard(str(self.completed_today), "Sessions today")
        metrics.addWidget(self.today_metric)
        metrics.addWidget(MetricCard("1h 42m", "Focused"))
        right.addLayout(metrics)
        up_next = QLabel("UP NEXT", objectName="eyebrow")
        right.addWidget(up_next)
        right.addWidget(SessionRow("Deep work", "Project Modoroco", "50 min", True))
        right.addWidget(SessionRow("Recovery", "Step away & reset", "10 min"))
        right.addSpacing(4)
        intent = QFrame(objectName="card")
        intent_layout = QVBoxLayout(intent)
        intent_layout.setContentsMargins(19, 18, 19, 18)
        intent_layout.addWidget(QLabel("Daily intention"))
        note = QLabel("Build with clarity. Finish with care.")
        note.setObjectName("subtle")
        note.setWordWrap(True)
        intent_layout.addWidget(note)
        right.addWidget(intent)
        right.addStretch()
        body.addLayout(right, 2)
        content.addLayout(body, 1)
        return page

    def _insights_page(self) -> QWidget:
        page, content = self._page(
            "YOUR MOMENTUM",
            "Quiet progress, made visible.",
            "A thoughtful view of your rhythm this week.",
        )
        cards = QHBoxLayout()
        cards.addWidget(MetricCard("18", "Completed sessions"))
        cards.addWidget(MetricCard("7h 35m", "Deep focus", "#6857d9"))
        cards.addWidget(MetricCard("4 days", "Current streak", "#f2a03d"))
        content.addLayout(cards)
        content.addSpacing(22)
        graph = QFrame(objectName="card")
        graph_layout = QVBoxLayout(graph)
        graph_layout.setContentsMargins(24, 22, 24, 24)
        graph_layout.addWidget(QLabel("Weekly rhythm"))
        graph_layout.addSpacing(20)
        bars = QHBoxLayout()
        for day, value in (
            ("M", 72),
            ("T", 44),
            ("W", 88),
            ("T", 62),
            ("F", 78),
            ("S", 28),
            ("S", 10),
        ):
            column = QVBoxLayout()
            bar = QFrame()
            bar.setFixedWidth(34)
            bar.setFixedHeight(value * 2)
            bar.setStyleSheet(f"background:{RED if value > 30 else '#ddd8d1'}; border-radius:8px;")
            column.addStretch()
            column.addWidget(bar, 0, Qt.AlignmentFlag.AlignHCenter)
            day_label = QLabel(day)
            day_label.setObjectName("subtle")
            column.addWidget(day_label, 0, Qt.AlignmentFlag.AlignHCenter)
            bars.addLayout(column)
        graph_layout.addLayout(bars, 1)
        content.addWidget(graph, 1)
        return page

    def _routines_page(self) -> QWidget:
        page, content = self._page(
            "FOCUS, YOUR WAY",
            "Choose your rhythm.",
            "Purpose-built routines for different kinds of work.",
        )
        for title, detail, duration in (
            ("Classic craft", "25 focus · 5 restore · repeat 4×", "25 min"),
            ("Deep work", "Long-form concentration with a generous recovery", "50 min"),
            ("Study flow", "Focused learning paced for recall", "40 min"),
            ("Quick win", "A compact sprint for the task you keep avoiding", "15 min"),
        ):
            row = SessionRow(title, detail, duration)
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            content.addWidget(row)
        content.addStretch()
        return page

    def _settings_page(self) -> QWidget:
        page, content = self._page(
            "PREFERENCES", "Shape your space.", "Modoroco should work the way your attention does."
        )
        card = QFrame(objectName="card")
        card.setMaximumWidth(720)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        title = QLabel("Default focus length")
        title.setStyleSheet("font-size:16px; font-weight:650;")
        self.duration_value = QLabel(f"{int(self.snapshot.duration.total_seconds() // 60)} minutes")
        self.duration_value.setObjectName("subtle")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(10, 90)
        slider.setSingleStep(5)
        slider.setValue(int(self.snapshot.duration.total_seconds() // 60))
        slider.valueChanged.connect(self._preference_duration)
        layout.addWidget(title)
        layout.addWidget(self.duration_value)
        layout.addSpacing(10)
        layout.addWidget(slider)
        layout.addSpacing(20)
        tip = QLabel(
            "Timer state is based on authoritative UTC timestamps, so sleep, "
            "window minimization, and system load cannot make it drift."
        )
        tip.setWordWrap(True)
        tip.setObjectName("subtle")
        layout.addWidget(tip)
        content.addWidget(card)
        content.addStretch()
        return page

    def _page(self, eyebrow: str, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(44, 35, 44, 38)
        outer.setSpacing(8)
        outer.addWidget(QLabel(eyebrow, objectName="eyebrow"))
        outer.addWidget(QLabel(title, objectName="headline"))
        outer.addWidget(QLabel(subtitle, objectName="subtle"))
        outer.addSpacing(20)
        return page, outer

    def _build_shortcuts(self) -> None:
        toggle = QAction(self)
        toggle.setShortcut(QKeySequence(Qt.Key.Key_Space))
        toggle.triggered.connect(self._toggle)
        self.addAction(toggle)
        reset = QAction(self)
        reset.setShortcut(QKeySequence("R"))
        reset.triggered.connect(self._reset)
        self.addAction(reset)

    def _navigate(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for position, button in enumerate(self.nav_buttons):
            button.setChecked(position == index)

    def _choose_duration(self, minutes: int) -> None:
        if self.snapshot.state in {TimerState.READY, TimerState.COMPLETE}:
            self.snapshot = self.snapshot.with_duration(minutes)
            self._render_timer()

    def _preference_duration(self, value: int) -> None:
        rounded = max(10, round(value / 5) * 5)
        self.duration_value.setText(f"{rounded} minutes")
        self.settings.setValue("focus_minutes", rounded)
        if self.snapshot.state in {TimerState.READY, TimerState.COMPLETE}:
            self.snapshot = TimerSnapshot.minutes(rounded)
            self._render_timer()

    def _toggle(self) -> None:
        now = utc_now()
        if self.snapshot.state in {TimerState.READY, TimerState.COMPLETE}:
            self.snapshot = self.snapshot.start(now)
        elif self.snapshot.state is TimerState.RUNNING:
            self.snapshot = self.snapshot.pause(now)
        elif self.snapshot.state is TimerState.PAUSED:
            self.snapshot = self.snapshot.resume(now)
        self._render_timer()

    def _reset(self) -> None:
        self.snapshot = self.snapshot.reset()
        self._render_timer()

    def _complete(self) -> None:
        if self.snapshot.state in {TimerState.RUNNING, TimerState.PAUSED}:
            self.completed_today += 1
            self.settings.setValue("completed_today", self.completed_today)
        self.snapshot = self.snapshot.reset()
        self._render_timer()

    def _tick(self) -> None:
        previous = self.snapshot.state
        self.snapshot = self.snapshot.reconcile(utc_now())
        if previous is TimerState.RUNNING and self.snapshot.state is TimerState.COMPLETE:
            self.completed_today += 1
            self.settings.setValue("completed_today", self.completed_today)
            QApplication.beep()
        self._render_timer()

    def _render_timer(self) -> None:
        remaining = self.snapshot.remaining(utc_now())
        seconds = max(0, int(remaining.total_seconds() + 0.999))
        duration_seconds = self.snapshot.duration.total_seconds()
        progress = seconds / duration_seconds if duration_seconds else 0
        text = f"{seconds // 60:02d}:{seconds % 60:02d}"
        labels = {
            TimerState.READY: ("READY TO FOCUS", "Begin focus"),
            TimerState.RUNNING: ("PROTECT THIS MOMENT", "Pause"),
            TimerState.PAUSED: ("PAUSED — BREATHE", "Continue"),
            TimerState.COMPLETE: ("BEAUTIFULLY DONE", "Begin again"),
        }
        caption, action = labels[self.snapshot.state]
        self.dial.display(text, caption, progress)
        self.action_button.setText(action)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Modoroco")
    app.setOrganizationName("The 1807")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    window = ModorocoWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
