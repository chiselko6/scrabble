FROM python:3.8.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
ENV PATH=/root/.poetry/bin:$PATH

RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

COPY scrabble/ ./scrabble/
COPY run_cmd.py ./
