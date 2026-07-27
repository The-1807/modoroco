from __future__ import annotations

import ast
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
SERVER_SOURCE = ROOT / "src" / "modoroco"
CORE_SOURCE = SERVER_SOURCE / "domain"


def imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for source in path.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".", 1)[0])
    return roots


def project_configuration() -> dict[str, object]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_dependency_groups_are_separated_by_runtime() -> None:
    project = project_configuration()["project"]
    assert isinstance(project, dict)
    extras = project["optional-dependencies"]
    assert isinstance(extras, dict)
    server = "\n".join(extras["server"]).lower()
    desktop = "\n".join(extras["desktop"]).lower()
    assert "pyside6" not in server
    assert "pytest" not in server
    assert "pyside6" in desktop
    assert project["dependencies"] == []


def test_server_source_does_not_import_desktop_runtime() -> None:
    imports = imported_roots(SERVER_SOURCE)
    assert "PySide6" not in imports
    assert "modoroco_ui" not in imports


def test_core_domain_has_no_framework_dependency() -> None:
    imports = imported_roots(CORE_SOURCE)
    assert imports.isdisjoint(
        {
            "PySide6",
            "fastapi",
            "pydantic",
            "sqlalchemy",
            "starlette",
        }
    )
