poetry run isort
poetry run flake8 scrabble/ tests/ app.py run_cmd.py
poetry run mypy --ignore-missing-imports scrabble/ tests/ app.py run_cmd.py
