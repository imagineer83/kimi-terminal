.PHONY: install test lint run clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check kimi_terminal tests
	mypy kimi_terminal

run:
	python -m kimi_terminal

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
