FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN mkdir -p /app/.uv-cache && chown -R appuser:appgroup /app

USER appuser

ENV UV_CACHE_DIR=/app/.uv-cache

CMD ["sh", "-c", "HTTP_PORT=${PORT:-8000} uv run python main.py --transport http"]
