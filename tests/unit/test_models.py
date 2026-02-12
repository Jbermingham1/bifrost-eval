"""Tests for evaluation data models."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from bifrost_eval.models.evaluation import (
    CostBreakdown,
    EvalResult,
    EvalScore,
    EvalSuite,
    GradeLevel,
    LatencyBreakdown,
    Scenario,
    ScenarioOutcome,
    ToolCallRecord,
)


class TestToolCallRecord:
    def test_default_values(self) -> None:
        record = ToolCallRecord(tool_name="test-tool")
        assert record.tool_name == "test-tool"
        assert record.success is True
        assert record.error is None
        assert record.duration_ms == 0.0
        assert record.arguments == {}

    def test_with_error(self) -> None:
        record = ToolCallRecord(
            tool_name="fail-tool", success=False, error="connection timeout"
        )
        assert not record.success
        assert record.error == "connection timeout"

    def test_with_cost(self) -> None:
        record = ToolCallRecord(tool_name="llm-call", cost_usd=0.05, token_count=1000)
        assert record.cost_usd == 0.05
        assert record.token_count == 1000


class TestCostBreakdown:
    def test_defaults(self) -> None:
        cost = CostBreakdown()
        assert cost.total_usd == 0.0
        assert cost.per_agent == {}
        assert cost.per_tool == {}

    def test_per_agent_tracking(self) -> None:
        cost = CostBreakdown(
            total_usd=0.15,
            per_agent={"agent-a": 0.10, "agent-b": 0.05},
        )
        assert cost.per_agent["agent-a"] == 0.10
        assert sum(cost.per_agent.values()) == pytest.approx(0.15)


class TestLatencyBreakdown:
    def test_defaults(self) -> None:
        latency = LatencyBreakdown()
        assert latency.total_ms == 0.0
        assert latency.p50_ms == 0.0

    def test_percentiles(self) -> None:
        latency = LatencyBreakdown(total_ms=5000, p50_ms=100, p95_ms=500, p99_ms=2000)
        assert latency.p95_ms > latency.p50_ms
        assert latency.p99_ms > latency.p95_ms


class TestEvalScore:
    def test_valid_score(self) -> None:
        score = EvalScore(name="accuracy", value=0.85, weight=1.0)
        assert score.value == 0.85

    def test_score_bounds(self) -> None:
        with pytest.raises(ValueError):
            EvalScore(name="test", value=1.5)
        with pytest.raises(ValueError):
            EvalScore(name="test", value=-0.1)

    @given(st.floats(min_value=0.0, max_value=1.0))
    def test_score_in_valid_range(self, value: float) -> None:
        score = EvalScore(name="prop-test", value=value)
        assert 0.0 <= score.value <= 1.0


class TestScenarioOutcome:
    def test_weighted_score_empty(self) -> None:
        outcome = ScenarioOutcome(scenario_name="test", passed=True)
        assert outcome.weighted_score == 0.0

    def test_weighted_score_single(self) -> None:
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.8, weight=1.0)],
        )
        assert outcome.weighted_score == pytest.approx(0.8)

    def test_weighted_score_multiple(self) -> None:
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[
                EvalScore(name="acc", value=1.0, weight=2.0),
                EvalScore(name="speed", value=0.5, weight=1.0),
            ],
        )
        expected = (1.0 * 2.0 + 0.5 * 1.0) / (2.0 + 1.0)
        assert outcome.weighted_score == pytest.approx(expected)

    def test_weighted_score_zero_weight(self) -> None:
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.8, weight=0.0)],
        )
        assert outcome.weighted_score == 0.0

    def test_tool_call_names(self) -> None:
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            tool_calls=[
                ToolCallRecord(tool_name="a"),
                ToolCallRecord(tool_name="b"),
                ToolCallRecord(tool_name="c"),
            ],
        )
        assert outcome.tool_call_names == ["a", "b", "c"]

    def test_tool_call_names_empty(self) -> None:
        outcome = ScenarioOutcome(scenario_name="test", passed=True)
        assert outcome.tool_call_names == []


class TestScenario:
    def test_basic_scenario(self) -> None:
        s = Scenario(name="test", description="a test")
        assert s.name == "test"
        assert s.timeout_ms == 30000.0
        assert s.expected_tool_calls == []

    def test_with_expected(self) -> None:
        s = Scenario(
            name="tool-test",
            expected_output=42,
            expected_tool_calls=["calc", "format"],
        )
        assert s.expected_output == 42
        assert len(s.expected_tool_calls) == 2


class TestEvalResult:
    def test_pass_rate_empty(self) -> None:
        result = EvalResult(suite_name="test")
        assert result.pass_rate == 0.0

    def test_pass_rate_all_pass(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(scenario_name="a", passed=True),
                ScenarioOutcome(scenario_name="b", passed=True),
            ],
        )
        assert result.pass_rate == 1.0

    def test_pass_rate_mixed(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(scenario_name="a", passed=True),
                ScenarioOutcome(scenario_name="b", passed=False),
            ],
        )
        assert result.pass_rate == 0.5

    def test_mean_score(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(
                    scenario_name="a",
                    passed=True,
                    scores=[EvalScore(name="acc", value=0.8)],
                ),
                ScenarioOutcome(
                    scenario_name="b",
                    passed=True,
                    scores=[EvalScore(name="acc", value=0.6)],
                ),
            ],
        )
        assert result.mean_score == pytest.approx(0.7)

    def test_grade_excellent(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(
                    scenario_name="a",
                    passed=True,
                    scores=[EvalScore(name="acc", value=0.95)],
                ),
            ],
        )
        assert result.grade == GradeLevel.EXCELLENT

    def test_grade_fail(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(
                    scenario_name="a",
                    passed=False,
                    scores=[EvalScore(name="acc", value=0.2)],
                ),
            ],
        )
        assert result.grade == GradeLevel.FAIL

    def test_passed_failed_counts(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(scenario_name="a", passed=True),
                ScenarioOutcome(scenario_name="b", passed=False),
                ScenarioOutcome(scenario_name="c", passed=True),
            ],
        )
        assert result.passed_count == 2
        assert result.failed_count == 1

    def test_grade_good(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(
                    scenario_name="a",
                    passed=True,
                    scores=[EvalScore(name="acc", value=0.8)],
                ),
            ],
        )
        assert result.grade == GradeLevel.GOOD

    def test_grade_acceptable(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(
                    scenario_name="a",
                    passed=True,
                    scores=[EvalScore(name="acc", value=0.65)],
                ),
            ],
        )
        assert result.grade == GradeLevel.ACCEPTABLE

    def test_grade_poor(self) -> None:
        result = EvalResult(
            suite_name="test",
            outcomes=[
                ScenarioOutcome(
                    scenario_name="a",
                    passed=True,
                    scores=[EvalScore(name="acc", value=0.45)],
                ),
            ],
        )
        assert result.grade == GradeLevel.POOR


class TestEvalSuite:
    def test_basic_suite(self) -> None:
        suite = EvalSuite(name="my-suite", scenarios=[Scenario(name="s1")])
        assert suite.name == "my-suite"
        assert len(suite.scenarios) == 1

    def test_empty_suite(self) -> None:
        suite = EvalSuite(name="empty")
        assert suite.scenarios == []
