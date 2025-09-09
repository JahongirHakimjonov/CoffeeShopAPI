# syntax=docker/dockerfile:1.2
ARG PYTHON_VERSION=3.11
ARG UV_VERSION=0.7.2

# small image that provides the uv tooling
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# builder stage: use uv to create venv and install deps
FROM python:${PYTHON_VERSION} AS builder
# copy uv tools into builder so uv commands work here too
COPY --from=uv /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONBUFFERED=1

WORKDIR /app

# create venv using uv and install dependencies into it
RUN uv venv /app/.venv
COPY ./pyproject.toml ./uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project --group docker

# final runtime image - copy venv + uv there so runtime scripts can call uv
FROM python:${PYTHON_VERSION}-slim AS app

WORKDIR /app

# bring uv runtime binary into the final image (so scripts that call `uv` will work)
# copy the exact files we need from the uv image
COPY --from=uv /uv /uvx /bin/

ENV PYTHONBUFFERED=1 \
    PYTHONPATH=$PYTHONPATH:/app/src \
    PATH=/app/.venv/bin:/bin:$PATH

# runtime-only deps (keep minimal)
RUN pip install --no-cache-dir --upgrade pip psycopg2-binary

# copy entry/start scripts (they call uv)
COPY ./deployments/compose/backend/celery/worker/start /start-celeryworker
COPY ./deployments/compose/backend/celery/beat/start /start-celerybeat
COPY ./deployments/compose/backend/entrypoint /entrypoint
COPY ./deployments/compose/backend/start /start

# strip CRLF and make executable
RUN sed -i 's/\r$//g' /start-celeryworker /start-celerybeat /entrypoint /start && \
    chmod +x /start-celeryworker /start-celerybeat /entrypoint /start

# copy the venv produced in the builder stage
COPY --from=builder /app/.venv .venv

# project files
COPY ./pyproject.toml ./uv.lock ./alembic.ini ./
COPY . .

# permissions as before
RUN chgrp -R 0 /app && chmod -R g=u /app

EXPOSE 8000

ENTRYPOINT ["/entrypoint"]
