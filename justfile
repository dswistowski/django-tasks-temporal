default:
    @just --list

lint: mypy ruff

ruff: ruff-format ruff-check

ruff-check:
    uv run ruff check --fix

ruff-format:
    uv run ruff format

mypy:
    PYTHONPATH="tests" DJANGO_SETTINGS_MODULE="django_app.settings" uv run mypy --strict .

worker:
    PYTHONPATH="tests" DJANGO_SETTINGS_MODULE="django_app.settings" uv run python -m django_tasks_temporal.worker

infra-up:
    docker compose -p django_tasks_temporal up -d
infra-down:
    docker compose -p django_tasks_temporal down

test:
    uv run pytest -v --tb=short --disable-warnings ./tests
