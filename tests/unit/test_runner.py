"""Tests for the evaluation runner."""

from __future__ import annotations

import pytest

from bifrost_eval.core.metrics import AccuracyMetric, LatencyMetric, ToolCorrectnessMetric
from bifrost_eval.core.runner import EvalRunner, ExecutionTrace, _percentile
from bifrost_eval.models.evaluation import (
    CostBreakdown,
    EvalSuite,
    LatencyBreakdown,
    Scenario,
    ToolCallRecord,
)
from tests.conftest import MockExecutor


class TestEvalRunner:
    @pytest.mark.asyncio
    async def test_run_single_scenario(self, simple_scenario: Scenario) -> None:
        executor = MockExecutor(output="result")
        runner = EvalRunner(
            executor=executor,
            metrics=[AccuracyMetric()],
        )
        outcome = await runner.run_scenario(simple_scenario)
        assert outcome.scenario_name == "test-scenario"
        assert outcome.passed is True
        assert executor.call_count == 1

    @pytest.mark.asyncio
    async def test_run_scenario_with_failure(self, simple_scenario: Scenario) -> None:
        executor = MockExecutor(output="wrong", success=False)
        runner = EvalRunner(
            executor=executor,
            metrics=[AccuracyMetric()],
        )
        outcome = await runner.run_scenario(simple_scenario)
        assert outcome.actual_output == "wrong"

    @pytest.mark.asyncio
    async def test_run_scenario_exception(self, simple_scenario: Scenario) -> None:
        executor = MockExecutor(raise_error=RuntimeError("boom"))
        runner = EvalRunner(executor=executor)
        outcome = await runner.run_scenario(simple_scenario)
        assert outcome.passed is False
        assert "boom" in (outcome.error or "")

    @pytest.mark.asyncio
    async def test_run_scenario_timeout(self) -> None:
        executor = MockExecutor(delay_ms=5000)
        scenario = Scenario(name="slow", timeout_ms=100)
        runner = EvalRunner(executor=executor)
        outcome = await runner.run_scenario(scenario)
        assert outcome.passed is False
        assert "Timeout" in (outcome.error or "")

    @pytest.mark.asyncio
    async def test_run_suite(self, simple_suite: EvalSuite) -> None:
        executor = MockExecutor(output="result")
        runner = EvalRunner(
            executor=executor,
            metrics=[AccuracyMetric()],
        )
        result = await runner.run_suite(simple_suite)
        assert result.suite_name == "test-suite"
        assert len(result.outcomes) == 1
        assert result.pass_rate > 0

    @pytest.mark.asyncio
    async def test_run_suite_multiple(self, multi_scenario_suite: EvalSuite) -> None:
        executor = MockExecutor(output=10)
        runner = EvalRunner(
            executor=executor,
            metrics=[AccuracyMetric()],
        )
        result = await runner.run_suite(multi_scenario_suite)
        assert len(result.outcomes) == 3
        # First scenario expects 10, executor returns 10 → pass
        # Others expect 20, 30 → fail
        assert result.passed_count >= 1

    @pytest.mark.asyncio
    async def test_run_suite_concurrent(self, multi_scenario_suite: EvalSuite) -> None:
        executor = MockExecutor(output=10)
        runner = EvalRunner(
            executor=executor,
            metrics=[AccuracyMetric()],
            max_concurrency=3,
        )
        result = await runner.run_suite(multi_scenario_suite)
        assert len(result.outcomes) == 3
        assert executor.call_count == 3

    @pytest.mark.asyncio
    async def test_multiple_metrics(self, simple_scenario: Scenario) -> None:
        executor = MockExecutor(
            output="result",
            tool_calls=[
                ToolCallRecord(tool_name="agent-a"),
                ToolCallRecord(tool_name="agent-b"),
            ],
            latency=LatencyBreakdown(total_ms=2000),
        )
        runner = EvalRunner(
            executor=executor,
            metrics=[
                AccuracyMetric(),
                ToolCorrectnessMetric(),
                LatencyMetric(target_ms=5000),
            ],
        )
        outcome = await runner.run_scenario(simple_scenario)
        assert len(outcome.scores) == 3
        score_names = {s.name for s in outcome.scores}
        assert "accuracy" in score_names
        assert "tool_correctness" in score_names
        assert "latency" in score_names

    @pytest.mark.asyncio
    async def test_cost_aggregation(self, multi_scenario_suite: EvalSuite) -> None:
        executor = MockExecutor(
            output=10,
            cost=CostBreakdown(total_usd=0.05),
        )
        runner = EvalRunner(executor=executor)
        result = await runner.run_suite(multi_scenario_suite)
        assert result.total_cost.total_usd == pytest.approx(0.15)

    @pytest.mark.asyncio
    async def test_latency_fallback(self, simple_scenario: Scenario) -> None:
        """When trace has no latency, runner should use measured time."""
        executor = MockExecutor(output="result")
        runner = EvalRunner(executor=executor)
        outcome = await runner.run_scenario(simple_scenario)
        assert outcome.latency.total_ms > 0


class TestPercentile:
    def test_single_value(self) -> None:
        assert _percentile([100.0], 50) == 100.0

    def test_two_values(self) -> None:
        assert _percentile([0.0, 100.0], 50) == pytest.approx(50.0)

    def test_empty(self) -> None:
        assert _percentile([], 50) == 0.0

    def test_p99_of_many(self) -> None:
        values = sorted(float(i) for i in range(100))
        p99 = _percentile(values, 99)
        assert p99 >= 98.0

    def test_p50(self) -> None:
        values = sorted([10.0, 20.0, 30.0, 40.0, 50.0])
        p50 = _percentile(values, 50)
        assert p50 == pytest.approx(30.0)


class TestExecutionTrace:
    def test_defaults(self) -> None:
        trace = ExecutionTrace()
        assert trace.output is None
        assert trace.tool_calls == []
        assert trace.success is True
        assert trace.error is None

    def test_with_data(self) -> None:
        trace = ExecutionTrace(
            output="hello",
            tool_calls=[ToolCallRecord(tool_name="t1")],
            cost=CostBreakdown(total_usd=0.01),
            latency=LatencyBreakdown(total_ms=100),
            success=True,
        )
        assert trace.output == "hello"
        assert len(trace.tool_calls) == 1
        assert trace.cost.total_usd == 0.01
