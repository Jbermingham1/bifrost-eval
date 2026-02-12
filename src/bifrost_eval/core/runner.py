"""Evaluation runner — executes scenarios and collects results."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Protocol

from bifrost_eval.core.scorer import Scorer
from bifrost_eval.models.evaluation import (
    CostBreakdown,
    EvalResult,
    EvalSuite,
    LatencyBreakdown,
    Scenario,
    ScenarioOutcome,
    ToolCallRecord,
)

if TYPE_CHECKING:
    from bifrost_eval.core.metrics import Metric


class PipelineExecutor(Protocol):
    """Protocol for executing a pipeline against a scenario.

    Implement this to connect bifrost-eval to your agent framework.
    """

    async def execute(self, scenario: Scenario) -> ExecutionTrace:
        """Execute the pipeline for the given scenario and return a trace."""
        ...


class ExecutionTrace:
    """Trace of a pipeline execution — output, tool calls, cost, latency."""

    def __init__(
        self,
        output: Any = None,
        tool_calls: list[ToolCallRecord] | None = None,
        cost: CostBreakdown | None = None,
        latency: LatencyBreakdown | None = None,
        error: str | None = None,
        success: bool = True,
    ):
        self.output = output
        self.tool_calls = tool_calls or []
        self.cost = cost or CostBreakdown()
        self.latency = latency or LatencyBreakdown()
        self.error = error
        self.success = success


class EvalRunner:
    """Runs evaluation suites against a pipeline executor."""

    def __init__(
        self,
        executor: PipelineExecutor,
        metrics: list[Metric] | None = None,
        scorer: Scorer | None = None,
        max_concurrency: int = 1,
    ):
        self.executor = executor
        self.metrics = metrics or []
        self.scorer = scorer or Scorer()
        self.max_concurrency = max_concurrency

    async def run_scenario(self, scenario: Scenario) -> ScenarioOutcome:
        """Run a single scenario and produce a scored outcome."""
        start = time.monotonic()

        try:
            trace = await asyncio.wait_for(
                self.executor.execute(scenario),
                timeout=scenario.timeout_ms / 1000.0,
            )
        except TimeoutError:
            elapsed = (time.monotonic() - start) * 1000
            return ScenarioOutcome(
                scenario_name=scenario.name,
                passed=False,
                error=f"Timeout after {elapsed:.0f}ms (limit: {scenario.timeout_ms}ms)",
                latency=LatencyBreakdown(total_ms=elapsed),
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return ScenarioOutcome(
                scenario_name=scenario.name,
                passed=False,
                error=str(exc),
                latency=LatencyBreakdown(total_ms=elapsed),
            )

        elapsed = (time.monotonic() - start) * 1000
        if trace.latency.total_ms <= 0:
            trace.latency.total_ms = elapsed

        outcome = ScenarioOutcome(
            scenario_name=scenario.name,
            passed=trace.success,
            actual_output=trace.output,
            tool_calls=trace.tool_calls,
            cost=trace.cost,
            latency=trace.latency,
            error=trace.error,
        )

        # Apply metrics
        for metric in self.metrics:
            expected = _get_expected_for_metric(metric, scenario)
            score = metric.score(outcome, expected)
            outcome.scores.append(score)

        # Apply grading
        self.scorer.apply_grade(outcome)
        return outcome

    async def run_suite(self, suite: EvalSuite) -> EvalResult:
        """Run all scenarios in a suite and produce aggregated results."""
        if self.max_concurrency <= 1:
            outcomes = []
            for scenario in suite.scenarios:
                outcome = await self.run_scenario(scenario)
                outcomes.append(outcome)
        else:
            sem = asyncio.Semaphore(self.max_concurrency)

            async def run_with_sem(scenario: Scenario) -> ScenarioOutcome:
                async with sem:
                    return await self.run_scenario(scenario)

            outcomes = list(
                await asyncio.gather(*[run_with_sem(s) for s in suite.scenarios])
            )

        total_cost = _aggregate_costs(outcomes)
        total_latency = _aggregate_latencies(outcomes)

        return EvalResult(
            suite_name=suite.name,
            outcomes=outcomes,
            total_cost=total_cost,
            total_latency=total_latency,
        )


def _get_expected_for_metric(metric: Metric, scenario: Scenario) -> Any:
    """Extract the expected value for a specific metric from a scenario."""
    if metric.name == "accuracy":
        return scenario.expected_output
    if metric.name == "tool_correctness":
        return scenario.expected_tool_calls
    return None


def _aggregate_costs(outcomes: list[ScenarioOutcome]) -> CostBreakdown:
    """Sum costs across all outcomes."""
    total = CostBreakdown()
    for o in outcomes:
        total.total_usd += o.cost.total_usd
        total.input_tokens += o.cost.input_tokens
        total.output_tokens += o.cost.output_tokens
        total.input_cost_usd += o.cost.input_cost_usd
        total.output_cost_usd += o.cost.output_cost_usd
        for agent, cost in o.cost.per_agent.items():
            total.per_agent[agent] = total.per_agent.get(agent, 0.0) + cost
        for tool, cost in o.cost.per_tool.items():
            total.per_tool[tool] = total.per_tool.get(tool, 0.0) + cost
    return total


def _aggregate_latencies(outcomes: list[ScenarioOutcome]) -> LatencyBreakdown:
    """Aggregate latency stats across outcomes."""
    if not outcomes:
        return LatencyBreakdown()

    times = sorted(o.latency.total_ms for o in outcomes)
    total = LatencyBreakdown(
        total_ms=sum(times),
        p50_ms=_percentile(times, 50),
        p95_ms=_percentile(times, 95),
        p99_ms=_percentile(times, 99),
    )
    for o in outcomes:
        for agent, ms in o.latency.per_agent.items():
            total.per_agent[agent] = total.per_agent.get(agent, 0.0) + ms
        for tool, ms in o.latency.per_tool.items():
            total.per_tool[tool] = total.per_tool.get(tool, 0.0) + ms
    return total


def _percentile(sorted_values: list[float], pct: int) -> float:
    """Calculate percentile from sorted values."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_values):
        return sorted_values[-1]
    d = k - f
    return sorted_values[f] + d * (sorted_values[c] - sorted_values[f])
