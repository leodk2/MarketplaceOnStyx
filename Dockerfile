FROM ghcr.io/astral-sh/uv:0.12.7-python3.14-trixie-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system styx \
    && useradd --system --gid styx --create-home styx \
    && mkdir /app \
    && chown styx:styx /app

USER styx
WORKDIR /app

# Install third-party dependencies in a cacheable layer. The Styx manifest is
# required to validate the workspace lockfile, but its source is copied later.
COPY --chown=styx:styx pyproject.toml uv.lock ./
COPY --chown=styx:styx styx-package/pyproject.toml styx-package/pyproject.toml
RUN uv sync --frozen --no-install-workspace

COPY --chown=styx:styx . .
RUN uv sync --locked

EXPOSE 3000

CMD ["uv", "run", "--no-sync", "python", "main.py"]
