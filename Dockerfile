FROM python:3.8.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl

ENV POETRY_VERSION=1.5.1 \
    POETRY_HOME=/opt/poetry \
    PATH=/opt/poetry/bin:$PATH
RUN curl -sSL https://install.python-poetry.org | python - && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

COPY scrabble/ ./scrabble/
COPY run_cmd.py ./
