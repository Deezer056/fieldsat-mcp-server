# syntax=docker/dockerfile:1
# FieldSat MCP server in demo mode (deterministic fixtures, no Copernicus keys).
FROM ghcr.io/astral-sh/uv:0.13.7 AS uv

FROM python:3.12-slim-bookworm AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-editable

FROM python:3.12-slim-bookworm
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 HOME=/tmp
USER app
EXPOSE 8001
# FieldSat has no /health route, so the check is "the port accepts connections".
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import socket; socket.create_connection(('127.0.0.1', 8001), 2)"]
# fieldsat.testing:app = the demo server, stateless Streamable HTTP, served at /mcp.
CMD ["uvicorn", "fieldsat.testing:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]