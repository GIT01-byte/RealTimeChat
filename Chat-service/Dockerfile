FROM python:3.14-slim

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction

COPY . /app/

EXPOSE 8001