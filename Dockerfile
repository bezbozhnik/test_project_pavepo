FROM python:3.12.7-alpine3.20 AS base

FROM base AS builder
RUN apk update && apk add --no-cache build-base bash curl git libstdc++ musl-dev cargo && \
    apk add --no-cache postgresql-dev

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /build/

ENV PATH="/root/.local/bin/:$PATH"
ENV UV_SYSTEM_PYTHON=1

COPY pyproject.toml uv.lock /build/

RUN uv sync --frozen --no-dev --no-install-project --no-editable --compile-bytecode --link-mode=copy
    RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --no-editable --compile-bytecode --link-mode=copy


RUN sed -i -r "s#!/build/.venv/bin/python#! /usr/local/bin/python#g" .venv/bin/*
RUN mv .venv /opt/venv
WORKDIR /app
COPY pyproject.toml /app/

COPY . .

FROM base AS final

RUN apk add --no-cache bash

COPY --from=builder /root/.local /root/.local

COPY --from=builder /app /app
COPY --from=builder /opt/venv/bin /opt/venv/bin
COPY --from=builder /opt/venv/lib/python3.12/site-packages/ /opt/venv/lib
COPY logging.ini /app/logging.ini

ENV PYTHONUNBUFFERED=1
ENV PATH=$HOME/.gauge:/opt/venv/bin/:$PATH
ENV PYTHONPATH="/opt/venv/lib/:/app/"
RUN chmod +x /app/scripts/makemigration.sh /app/scripts/migrate.sh /app/scripts/start.sh
WORKDIR /app/
