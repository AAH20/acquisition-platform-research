.PHONY: install test lint typecheck format clean benchmark all

install:
	pip install -e '.[dev]'

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

typecheck:
	mypy src/acquisition_platform/

format:
	ruff format src/ tests/

clean:
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name 'htmlcov' -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage coverage.xml 2>/dev/null || true
	rm -rf dist/ build/ 2>/dev/null || true

benchmark:
	python -m pytest tests/ --benchmark-only

all: install test lint typecheck
