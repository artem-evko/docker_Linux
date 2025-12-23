# syntax=docker/dockerfile:1.6

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# ---------- build stage ----------
FROM base AS builder
# wheel иногда не установлен в slim, поставим (без upgrade)
RUN python -m pip install --no-cache-dir wheel

COPY pyproject.toml ./
RUN python -m pip wheel --wheel-dir /wheels .
RUN python -m pip wheel --wheel-dir /wheels-test ".[test]"

# ---------- runtime stage ----------
FROM base AS prod
RUN adduser --disabled-password --gecos "" appuser

COPY --from=builder /wheels /wheels
RUN python -m pip install --no-index --find-links=/wheels KubSU && rm -rf /wheels

COPY src ./src

ENV PYTHONPATH=/app \
    ROOT_PATH=""
EXPOSE 8008

USER appuser
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8008"]

# ---------- test stage (тесты запускаются внутри собранного image) ----------
FROM prod AS test
USER root
COPY --from=builder /wheels-test /wheels-test
RUN python -m pip install --no-index --find-links=/wheels-test KubSU[test] && rm -rf /wheels-test
COPY tests ./tests
USER appuser
CMD ["pytest", "-q", "tests"]
