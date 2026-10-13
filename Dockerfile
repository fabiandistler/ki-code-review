FROM python:3.14-slim-trixie AS base
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

FROM base AS test
RUN uv sync --locked --no-install-project
COPY src ./src
COPY tests ./tests
COPY Dockerfile ./Dockerfile
COPY .github ./.github
RUN uv sync --locked
RUN uv run pytest -q

FROM base AS runtime
COPY src ./src
RUN uv sync --locked --no-dev
EXPOSE 8000
CMD ["uv", "run", "--no-dev", "python", "-m", "ki_review"]
