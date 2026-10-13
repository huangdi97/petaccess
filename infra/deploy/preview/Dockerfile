# syntax=docker/dockerfile:1.7
FROM python:3.12-slim-bookworm

# Pin uv: deployment images must not silently change their package manager.
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# The lockfile is workspace-wide, so keep every workspace member manifest
# available even though this image syncs only the API package.
COPY pyproject.toml uv.lock ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/worker/pyproject.toml services/worker/pyproject.toml
COPY services/api services/api
COPY services/worker services/worker

RUN uv sync --locked --no-dev --package petaccess-api --no-editable

COPY infra/deploy/preview/preview-env-check.sh /usr/local/bin/petaccess-preview-env-check
COPY infra/deploy/preview/entrypoint-api.sh /usr/local/bin/petaccess-preview-api
COPY infra/deploy/preview/entrypoint-worker.sh /usr/local/bin/petaccess-preview-worker
RUN chmod 0755 \
    /usr/local/bin/petaccess-preview-env-check \
    /usr/local/bin/petaccess-preview-api \
    /usr/local/bin/petaccess-preview-worker \
    && useradd --create-home --uid 10001 petaccess

USER petaccess

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c 'import os,urllib.request; urllib.request.urlopen("http://127.0.0.1:%s/health" % os.environ.get("PORT","8000"), timeout=3).read()'

ENTRYPOINT ["/usr/local/bin/petaccess-preview-api"]
