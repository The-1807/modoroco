# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.8.4 AS uv
FROM python:3.13.5-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13.5-slim AS runtime
LABEL org.opencontainers.image.title="Modoroco" org.opencontainers.image.licenses="Apache-2.0"
RUN useradd --create-home --uid 1807 modoroco
WORKDIR /app
COPY --from=builder --chown=modoroco:modoroco /build/.venv /app/.venv
COPY --chown=modoroco:modoroco migrations alembic.ini ./
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER modoroco
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/live', timeout=2)"]
CMD ["uvicorn", "modoroco.runtime.api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

