# Contributing to bifrost-eval

## Setup

```bash
git clone https://github.com/Jbermingham1/bifrost-eval.git
cd bifrost-eval
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Development

### Run tests
```bash
pytest tests/ -v
```

### Lint
```bash
ruff check src/ tests/
```

### Type check
```bash
pyright src/
```

### Security scan
```bash
bandit -r src/
pip-audit
```

## Adding a new metric

1. Create a class extending `Metric` in `src/bifrost_eval/core/metrics.py`
2. Implement the `score()` method
3. Add tests in `tests/unit/test_metrics.py`
4. Export from `src/bifrost_eval/core/__init__.py` and `src/bifrost_eval/__init__.py`

## Pull Requests

- All tests must pass
- Coverage must stay above 80%
- Type hints required on all functions
- One PR per feature/fix
