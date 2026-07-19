"""Visual tokens and Qt stylesheet for Modoroco."""

RED = "#ff3b3f"
RED_DARK = "#e7272c"
INK = "#20252d"
MUTED = "#777b83"
IVORY = "#f8f6f2"
PAPER = "#fffdfa"
BORDER = "#e9e5df"

STYLESHEET = f"""
* {{ font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif; color: {INK}; }}
QMainWindow, QWidget#root {{ background: {IVORY}; }}
QFrame#sidebar {{ background: {PAPER}; border-right: 1px solid {BORDER}; }}
QLabel#brand {{ font-size: 21px; font-weight: 700; letter-spacing: 1px; }}
QLabel#eyebrow {{ color: {RED}; font-size: 11px; font-weight: 700; letter-spacing: 2px; }}
QLabel#headline {{ font-size: 30px; font-weight: 700; }}
QLabel#subtle {{ color: {MUTED}; font-size: 13px; }}
QLabel#metric {{ font-size: 25px; font-weight: 700; }}
QLabel#metricLabel {{ color: {MUTED}; font-size: 11px; font-weight: 600; }}
QPushButton {{ border: 0; border-radius: 10px; padding: 10px 14px; font-weight: 600; }}
QPushButton:hover {{ background: #f0ece7; }}
QPushButton:pressed {{ background: #e8e2dc; }}
QPushButton#nav {{ text-align: left; color: {MUTED}; padding: 12px 14px; }}
QPushButton#nav:checked {{ color: {RED}; background: #fff0ee; }}
QPushButton#primary {{ background: {RED}; color: white; padding: 13px 24px; }}
QPushButton#primary:hover {{ background: {RED_DARK}; }}
QPushButton#round {{ background: {PAPER}; border: 1px solid {BORDER}; border-radius: 22px; }}
QFrame#card {{ background: {PAPER}; border: 1px solid {BORDER}; border-radius: 18px; }}
QFrame#sessionCard {{ background: #242932; border-radius: 18px; }}
QFrame#sessionCard QLabel {{ color: white; }}
QProgressBar {{ border: 0; background: #ebe7e1; border-radius: 3px; height: 6px; }}
QProgressBar::chunk {{ background: {RED}; border-radius: 3px; }}
QSlider::groove:horizontal {{ height: 5px; background: #e7e2dc; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {RED}; width: 18px; margin: -7px 0; border-radius: 9px; }}
QToolTip {{ background: {INK}; color: white; border: 0; padding: 6px; }}
"""
