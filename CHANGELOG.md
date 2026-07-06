# Changelog

## [0.2.0] - 2026-07-06

### Fixed
- **Metrics no longer treat missing data as a perfect score.** A dimension with
  nothing to measure (no cost data, no latency data, no expected output/tools)
  is now excluded from the weighted grade (weight 0) instead of scoring 1.0.
- **Tool correctness component weights now sum to 1.0** (presence 0.6 + order 0.4)
  — a perfect tool sequence previously could not score above 0.8.
- **AMFAdapter default output extraction** now returns the final agent's output;
  previously it returned the agent-name-keyed dict, which never matched a
  scenario's `expected_output`, grading correct pipelines as failures.
- `WeightedGrader` now fails an outcome when a required score dimension is
  missing instead of silently passing it.
- Bandit security scan in CI no longer masked (`|| true` removed); pip-audit
  scoped past the CI runner's own unfixable pip CVE.
- Author email corrected.

### Changed
- **BREAKING:** `ToolCorrectnessMetric(strict_order=...)` renamed to
  `check_order`, and order checking is now ON by default (the README always
  described LCS order scoring as core behaviour).
- **BREAKING:** CLI `run` stub removed — it could never execute (running a
  suite requires a `PipelineExecutor`, which only exists in Python code).
  `validate` and `--version` remain.
- Test coverage stated as measured: 88% at release (80% gate enforced in CI).

### Added
- Integration boundary tests that evaluate REAL agent-mcp-framework pipelines
  through `AMFAdapter` — the tests that would have caught the adapter and
  cost-scoring bugs. `agent-mcp-framework` added to dev dependencies so CI
  runs them.
- Explicit sdist contents (`only-include`) so published archives contain only
  source, tests, and docs.

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
