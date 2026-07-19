import uvicorn

from modoroco.interfaces.api import create_app

app = create_app()


def main() -> None:
    uvicorn.run("modoroco.runtime.api:app", host="0.0.0.0", port=8000)
