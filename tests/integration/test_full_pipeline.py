"""Integration tests — full evaluation pipeline end-to-end."""

from __future__ import annotations

import pytest

from bifrost_eval.adapters.comparison import ComparisonRunner
from bifrost_eval.core.metrics import (
    AccuracyMetric,
    CostEfficiencyMetric,
    LatencyMetric,
    ToolCorrectnessMetric,
)
from bifrost_eval.core.runner import EvalRunner, ExecutionTrace
from bifrost_eval.core.scorer import Scorer, ThresholdGrader, WeightedGrader
from bifrost_eval.models.evaluation import (
    CostBreakdown,
    EvalSuite,
    GradeLevel,
    LatencyBreakdown,
    Scenario,
    ToolCallRecord,
)
from tests.conftest import MockExecutor


class TestFullEvalPipeline:
    """End-to-end evaluation pipeline tests."""

    @pytest.mark.asyncio
    async def test_complete_evaluation_flow(self) -> None:
        """Test a full evaluation from suite definition to graded results."""
        suite = EvalSuite(
            name="e2e-test",
            scenarios=[
                Scenario(
                    name="basic-calc",
                    input_data={"expression": "2+2"},
                    expected_output=4,
                    expected_tool_calls=["calculator"],
                ),
                Scenario(
                    name="complex-calc",
                    input_data={"expression": "sqrt(16)"},
                    expected_output=4,
                    expected_tool_calls=["calculator", "formatter"],
                ),
            ],
        )

        executor = MockExecutor(
            output=4,
            tool_calls=[ToolCallRecord(tool_name="calculator")],
            cost=CostBreakdown(total_usd=0.02),
            latency=LatencyBreakdown(total_ms=500),
        )

        runner = EvalRunner(
            executor=executor,
            metrics=[
                AccuracyMetric(weight=2.0),
                ToolCorrectnessMetric(weight=1.0),
                LatencyMetric(target_ms=5000, weight=0.5),
                CostEfficiencyMetric(budget_usd=0.10, weight=0.5),
            ],
            scorer=Scorer(grader=ThresholdGrader()),
        )

        result = await runner.run_suite(suite)

        assert result.suite_name == "e2e-test"
        assert len(result.outcomes) == 2
        assert result.total_cost.total_usd == pytest.approx(0.04)
        assert result.pass_rate > 0
        assert result.grade in list(GradeLevel)

    @pytest.mark.asyncio
    async def test_ab_comparison_flow(self) -> None:
        """Test A/B comparison between two pipeline configurations."""
        suite = EvalSuite(
            name="ab-test",
            scenarios=[
                Scenario(name="s1", expected_output="correct"),
                Scenario(name="s2", expected_output="correct"),
                Scenario(name="s3", expected_output="correct"),
            ],
        )

        good_executor = MockExecutor(
            output="correct",
            cost=CostBreakdown(total_usd=0.05),
            latency=LatencyBreakdown(total_ms=200),
        )
        bad_executor = MockExecutor(
            output="wrong",
            cost=CostBreakdown(total_usd=0.01),
            latency=LatencyBreakdown(total_ms=50),
        )

        comparator = ComparisonRunner(
            metrics=[AccuracyMetric(weight=3.0), CostEfficiencyMetric(weight=1.0)],
        )

        result = await comparator.compare(
            suite,
            {"accurate-but-costly": good_executor, "cheap-but-wrong": bad_executor},
        )

        assert result.winner == "accurate-but-costly"
        assert result.summary["accurate-but-costly"]["pass_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_mixed_results(self) -> None:
        """Test suite with mixed passing and failing scenarios."""
        suite = EvalSuite(
            name="mixed",
            scenarios=[
                Scenario(name="pass-1", expected_output="ok"),
                Scenario(name="pass-2", expected_output="ok"),
                Scenario(name="fail-1", expected_output="different"),
            ],
        )

        executor = MockExecutor(output="ok")
        runner = EvalRunner(
            executor=executor,
            metrics=[AccuracyMetric()],
        )

        result = await runner.run_suite(suite)
        assert result.passed_count == 2
        assert result.failed_count == 1
        assert result.pass_rate == pytest.approx(2.0 / 3.0)

    @pytest.mark.asyncio
    async def test_weighted_grading_with_requirements(self) -> None:
        """Test that weighted grader enforces minimum scores."""
        suite = EvalSuite(
            name="weighted",
            scenarios=[
                Scenario(name="s1", expected_output="x"),
            ],
        )

        executor = MockExecutor(output="x")
        grader = WeightedGrader(required_scores={"accuracy": 0.9})
        runner = EvalRunner(
            executor=executor,
            metrics=[AccuracyMetric()],
            scorer=Scorer(grader=grader),
        )

        result = await runner.run_suite(suite)
        # Accuracy is 1.0, meets 0.9 requirement → should pass
        assert result.outcomes[0].passed is True

    @pytest.mark.asyncio
    async def test_concurrent_execution(self) -> None:
        """Test that concurrent execution produces same results as sequential."""
        suite = EvalSuite(
            name="concurrency",
            scenarios=[Scenario(name=f"s{i}", expected_output=i) for i in range(10)],
        )

        executor_seq = MockExecutor(output=5)
        executor_par = MockExecutor(output=5)

        runner_seq = EvalRunner(
            executor=executor_seq, metrics=[AccuracyMetric()], max_concurrency=1,
        )
        runner_par = EvalRunner(
            executor=executor_par, metrics=[AccuracyMetric()], max_concurrency=5,
        )

        result_seq = await runner_seq.run_suite(suite)
        result_par = await runner_par.run_suite(suite)

        assert result_seq.pass_rate == result_par.pass_rate
        assert result_seq.mean_score == pytest.approx(result_par.mean_score)

    @pytest.mark.asyncio
    async def test_error_recovery(self) -> None:
        """Test that errors in one scenario don't break the suite."""
        suite = EvalSuite(
            name="error-recovery",
            scenarios=[
                Scenario(name="ok-1", expected_output="fine"),
                Scenario(name="timeout", timeout_ms=50),
                Scenario(name="ok-2", expected_output="fine"),
            ],
        )

        class MixedExecutor:
            async def execute(self, scenario: Scenario) -> ExecutionTrace:
                if scenario.name == "timeout":
                    import asyncio
                    await asyncio.sleep(10)
                return ExecutionTrace(output="fine")

        runner = EvalRunner(
            executor=MixedExecutor(),  # type: ignore[arg-type]
            metrics=[AccuracyMetric()],
        )

        result = await runner.run_suite(suite)
        assert len(result.outcomes) == 3
        # 2 pass, 1 timeout
        assert result.passed_count >= 2
