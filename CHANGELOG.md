# Changelog

## [0.1.0] - 2026-02-12

### Added
- Core evaluation engine with pluggable metrics and scoring
- `AccuracyMetric` — exact match or custom comparator scoring
- `ToolCorrectnessMetric` — tool presence, order, and extras scoring
- `LatencyMetric` — speed vs target threshold scoring
- `CostEfficiencyMetric` — cost vs budget scoring
- `EvalRunner` — scenario and suite execution with concurrency support
- `Scorer` with `ThresholdGrader` and `WeightedGrader` strategies
- A/B `ComparisonRunner` for comparing pipeline configurations
- `AMFAdapter` for agent-mcp-framework integration
- CLI with `validate` command for suite file validation
- Pydantic models for all data structures
- Full type hints (py.typed marker)
- 111 tests with 90% coverage
- CI/CD pipeline with lint, type check, test, security scan, build, publish
