"""Tests for evaluation metrics."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from bifrost_eval.core.metrics import (
    AccuracyMetric,
    CostEfficiencyMetric,
    LatencyMetric,
    ToolCorrectnessMetric,
    _lcs_ratio,
)
from bifrost_eval.models.evaluation import (
    CostBreakdown,
    LatencyBreakdown,
    ScenarioOutcome,
    ToolCallRecord,
)


class TestAccuracyMetric:
    def test_exact_match(self) -> None:
        metric = AccuracyMetric()
        outcome = ScenarioOutcome(
            scenario_name="test", passed=True, actual_output="hello"
        )
        score = metric.score(outcome, expected="hello")
        assert score.value == 1.0
        assert score.name == "accuracy"

    def test_mismatch(self) -> None:
        metric = AccuracyMetric()
        outcome = ScenarioOutcome(
            scenario_name="test", passed=True, actual_output="hello"
        )
        score = metric.score(outcome, expected="world")
        assert score.value == 0.0

    def test_no_expected(self) -> None:
        metric = AccuracyMetric()
        outcome = ScenarioOutcome(
            scenario_name="test", passed=True, actual_output="hello"
        )
        score = metric.score(outcome, expected=None)
        assert score.value == 1.0

    def test_custom_comparator(self) -> None:
        def fuzzy(actual: object, expected: object) -> bool:
            return str(actual).lower() == str(expected).lower()

        metric = AccuracyMetric(comparator=fuzzy)
        outcome = ScenarioOutcome(
            scenario_name="test", passed=True, actual_output="HELLO"
        )
        score = metric.score(outcome, expected="hello")
        assert score.value == 1.0

    def test_weight(self) -> None:
        metric = AccuracyMetric(weight=2.0)
        outcome = ScenarioOutcome(
            scenario_name="test", passed=True, actual_output="x"
        )
        score = metric.score(outcome, expected="x")
        assert score.weight == 2.0

    def test_numeric_match(self) -> None:
        metric = AccuracyMetric()
        outcome = ScenarioOutcome(scenario_name="test", passed=True, actual_output=42)
        score = metric.score(outcome, expected=42)
        assert score.value == 1.0

    def test_dict_match(self) -> None:
        metric = AccuracyMetric()
        outcome = ScenarioOutcome(
            scenario_name="test", passed=True, actual_output={"a": 1}
        )
        score = metric.score(outcome, expected={"a": 1})
        assert score.value == 1.0


class TestToolCorrectnessMetric:
    def test_perfect_match(self) -> None:
        metric = ToolCorrectnessMetric()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            tool_calls=[
                ToolCallRecord(tool_name="a"),
                ToolCallRecord(tool_name="b"),
            ],
        )
        score = metric.score(outcome, expected=["a", "b"])
        assert score.value > 0.7

    def test_missing_tool(self) -> None:
        metric = ToolCorrectnessMetric()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            tool_calls=[ToolCallRecord(tool_name="a")],
        )
        score = metric.score(outcome, expected=["a", "b"])
        # Only 1 of 2 expected tools present → partial score
        assert score.value < 0.7

    def test_extra_tools(self) -> None:
        metric = ToolCorrectnessMetric()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            tool_calls=[
                ToolCallRecord(tool_name="a"),
                ToolCallRecord(tool_name="b"),
                ToolCallRecord(tool_name="c"),
            ],
        )
        score = metric.score(outcome, expected=["a", "b"])
        assert 0.0 < score.value <= 1.0

    def test_no_expected(self) -> None:
        metric = ToolCorrectnessMetric()
        outcome = ScenarioOutcome(scenario_name="test", passed=True)
        score = metric.score(outcome, expected=None)
        assert score.value == 1.0

    def test_empty_expected(self) -> None:
        metric = ToolCorrectnessMetric()
        outcome = ScenarioOutcome(scenario_name="test", passed=True)
        score = metric.score(outcome, expected=[])
        assert score.value == 1.0

    def test_strict_order_correct(self) -> None:
        metric = ToolCorrectnessMetric(strict_order=True)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            tool_calls=[
                ToolCallRecord(tool_name="a"),
                ToolCallRecord(tool_name="b"),
                ToolCallRecord(tool_name="c"),
            ],
        )
        score = metric.score(outcome, expected=["a", "b", "c"])
        assert score.value > 0.7

    def test_strict_order_wrong(self) -> None:
        metric = ToolCorrectnessMetric(strict_order=True)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            tool_calls=[
                ToolCallRecord(tool_name="c"),
                ToolCallRecord(tool_name="b"),
                ToolCallRecord(tool_name="a"),
            ],
        )
        score_wrong = metric.score(outcome, expected=["a", "b", "c"])
        # Correct order should score higher
        outcome_correct = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            tool_calls=[
                ToolCallRecord(tool_name="a"),
                ToolCallRecord(tool_name="b"),
                ToolCallRecord(tool_name="c"),
            ],
        )
        score_correct = metric.score(outcome_correct, expected=["a", "b", "c"])
        assert score_correct.value >= score_wrong.value

    def test_completely_wrong_tools(self) -> None:
        metric = ToolCorrectnessMetric()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            tool_calls=[
                ToolCallRecord(tool_name="x"),
                ToolCallRecord(tool_name="y"),
            ],
        )
        score = metric.score(outcome, expected=["a", "b"])
        # Zero presence + all extras → very low but order component still contributes
        assert score.value < 0.3


class TestLatencyMetric:
    def test_within_target(self) -> None:
        metric = LatencyMetric(target_ms=5000)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            latency=LatencyBreakdown(total_ms=2500),
        )
        score = metric.score(outcome)
        assert score.value == 1.0

    def test_at_target(self) -> None:
        metric = LatencyMetric(target_ms=5000)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            latency=LatencyBreakdown(total_ms=5000),
        )
        score = metric.score(outcome)
        assert score.value == pytest.approx(1.0)

    def test_over_target(self) -> None:
        metric = LatencyMetric(target_ms=5000)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            latency=LatencyBreakdown(total_ms=10000),
        )
        score = metric.score(outcome)
        assert score.value == pytest.approx(0.5)

    def test_no_latency_data(self) -> None:
        metric = LatencyMetric()
        outcome = ScenarioOutcome(scenario_name="test", passed=True)
        score = metric.score(outcome)
        assert score.value == 1.0

    @given(st.floats(min_value=1.0, max_value=100000.0))
    def test_score_always_valid(self, latency: float) -> None:
        metric = LatencyMetric(target_ms=5000)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            latency=LatencyBreakdown(total_ms=latency),
        )
        score = metric.score(outcome)
        assert 0.0 <= score.value <= 1.0


class TestCostEfficiencyMetric:
    def test_within_budget(self) -> None:
        metric = CostEfficiencyMetric(budget_usd=0.10)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            cost=CostBreakdown(total_usd=0.05),
        )
        score = metric.score(outcome)
        assert score.value == 1.0

    def test_at_budget(self) -> None:
        metric = CostEfficiencyMetric(budget_usd=0.10)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            cost=CostBreakdown(total_usd=0.10),
        )
        score = metric.score(outcome)
        assert score.value == pytest.approx(1.0)

    def test_over_budget(self) -> None:
        metric = CostEfficiencyMetric(budget_usd=0.10)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            cost=CostBreakdown(total_usd=0.20),
        )
        score = metric.score(outcome)
        assert score.value == pytest.approx(0.5)

    def test_no_cost_data(self) -> None:
        metric = CostEfficiencyMetric()
        outcome = ScenarioOutcome(scenario_name="test", passed=True)
        score = metric.score(outcome)
        assert score.value == 1.0

    @given(st.floats(min_value=0.001, max_value=10.0))
    def test_score_always_valid(self, cost: float) -> None:
        metric = CostEfficiencyMetric(budget_usd=0.10)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            cost=CostBreakdown(total_usd=cost),
        )
        score = metric.score(outcome)
        assert 0.0 <= score.value <= 1.0


class TestLcsRatio:
    def test_identical(self) -> None:
        assert _lcs_ratio(["a", "b", "c"], ["a", "b", "c"]) == pytest.approx(1.0)

    def test_reversed(self) -> None:
        ratio = _lcs_ratio(["a", "b", "c"], ["c", "b", "a"])
        assert ratio == pytest.approx(1.0 / 3.0)

    def test_empty_expected(self) -> None:
        assert _lcs_ratio([], ["a"]) == 0.0

    def test_empty_actual(self) -> None:
        assert _lcs_ratio(["a"], []) == 0.0

    def test_partial_match(self) -> None:
        ratio = _lcs_ratio(["a", "b", "c"], ["a", "x", "c"])
        assert ratio == pytest.approx(2.0 / 3.0)
