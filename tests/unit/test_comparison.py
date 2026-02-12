"""Tests for the comparison runner."""

from __future__ import annotations

import pytest

from bifrost_eval.adapters.comparison import ComparisonResult, ComparisonRunner
from bifrost_eval.core.metrics import AccuracyMetric
from bifrost_eval.models.evaluation import (
    CostBreakdown,
    EvalSuite,
    Scenario,
)
from tests.conftest import MockExecutor


class TestComparisonResult:
    def test_determine_winner_empty(self) -> None:
        result = ComparisonResult(suite_name="test")
        assert result.determine_winner() == ""

    def test_determine_winner(self) -> None:
        from bifrost_eval.models.evaluation import EvalResult, EvalScore, ScenarioOutcome

        result = ComparisonResult(
            suite_name="test",
            results={
                "config-a": EvalResult(
                    suite_name="test",
                    outcomes=[
                        ScenarioOutcome(
                            scenario_name="s1",
                            passed=True,
                            scores=[EvalScore(name="acc", value=0.9)],
                        )
                    ],
                ),
                "config-b": EvalResult(
                    suite_name="test",
                    outcomes=[
                        ScenarioOutcome(
                            scenario_name="s1",
                            passed=True,
                            scores=[EvalScore(name="acc", value=0.7)],
                        )
                    ],
                ),
            },
        )
        winner = result.determine_winner()
        assert winner == "config-a"
        assert result.winner == "config-a"
        assert "config-a" in result.summary
        assert "config-b" in result.summary


class TestComparisonRunner:
    @pytest.mark.asyncio
    async def test_compare_two_configs(self) -> None:
        suite = EvalSuite(
            name="comparison-test",
            scenarios=[
                Scenario(name="s1", expected_output="good"),
                Scenario(name="s2", expected_output="good"),
            ],
        )
        executor_a = MockExecutor(output="good")
        executor_b = MockExecutor(output="bad")

        runner = ComparisonRunner(metrics=[AccuracyMetric()])
        result = await runner.compare(
            suite,
            {"config-a": executor_a, "config-b": executor_b},
        )
        assert result.suite_name == "comparison-test"
        assert result.winner == "config-a"
        assert len(result.results) == 2

    @pytest.mark.asyncio
    async def test_compare_single_config(self) -> None:
        suite = EvalSuite(
            name="single",
            scenarios=[Scenario(name="s1", expected_output="ok")],
        )
        executor = MockExecutor(output="ok")

        runner = ComparisonRunner(metrics=[AccuracyMetric()])
        result = await runner.compare(suite, {"only": executor})
        assert result.winner == "only"

    @pytest.mark.asyncio
    async def test_compare_with_costs(self) -> None:
        suite = EvalSuite(
            name="cost-test",
            scenarios=[Scenario(name="s1", expected_output="ok")],
        )
        cheap = MockExecutor(output="ok", cost=CostBreakdown(total_usd=0.01))
        expensive = MockExecutor(output="ok", cost=CostBreakdown(total_usd=0.50))

        runner = ComparisonRunner(metrics=[AccuracyMetric()])
        result = await runner.compare(
            suite,
            {"cheap": cheap, "expensive": expensive},
        )
        # Both have same accuracy, summary should show cost difference
        cheap_cost = result.summary["cheap"]["total_cost_usd"]
        expensive_cost = result.summary["expensive"]["total_cost_usd"]
        assert cheap_cost < expensive_cost
