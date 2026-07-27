from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import os
from pathlib import Path

SERVER_MODULES = (
    "modoroco.domain",
    "modoroco.application.service",
    "modoroco.infrastructure.auth",
    "modoroco.infrastructure.config",
    "modoroco.infrastructure.database",
    "modoroco.interfaces.api",
    "modoroco.runtime.api",
    "modoroco.runtime.worker",
)
SERVER_FORBIDDEN_DISTRIBUTIONS = (
    "PySide6",
    "PySide6_Addons",
    "PySide6_Essentials",
    "shiboken6",
    "pytest",
    "hypothesis",
    "ruff",
    "pyright",
    "coverage",
)


def distribution_exists(name: str) -> bool:
    try:
        importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def verify_server() -> None:
    unexpected = [name for name in SERVER_FORBIDDEN_DISTRIBUTIONS if distribution_exists(name)]
    if unexpected:
        raise RuntimeError(f"server profile contains forbidden distributions: {unexpected}")
    for module in SERVER_MODULES:
        importlib.import_module(module)
    if not Path("migrations/env.py").is_file():
        raise RuntimeError("Alembic migration environment is unavailable")


def verify_desktop() -> None:
    if not distribution_exists("PySide6") or not distribution_exists("shiboken6"):
        raise RuntimeError("desktop profile does not contain the Qt runtime")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from modoroco_ui.app import ModorocoWindow

    application = QApplication.instance() or QApplication([])
    window = ModorocoWindow()
    window.show()
    application.processEvents()
    if not window.windowTitle():
        raise RuntimeError("desktop window did not initialize")
    window.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=("server", "desktop"))
    profile = parser.parse_args().profile
    if profile == "server":
        verify_server()
    else:
        verify_desktop()
    print(f"{profile} dependency profile verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
