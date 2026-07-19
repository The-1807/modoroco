from __future__ import annotations

import argparse
import json
from pathlib import Path

from modoroco.interfaces.api import create_app


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = Path("openapi/openapi.json")
    rendered = json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n"
    if args.check:
        return 0 if target.exists() and target.read_text(encoding="utf-8") == rendered else 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
