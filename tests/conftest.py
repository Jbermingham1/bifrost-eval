"""Shared test fixtures for bifrost-eval."""

from __future__ import annotations

import pytest

from bifrost_eval.core.runner import ExecutionTrace
from bifrost_eval.models.evaluation import (
    CostBreakdown,
    EvalSuite,
    LatencyBreakdown,
    Scenario,
    ToolCallRecord,
)


class MockExecutor:
    """Mock pipeline executor for testing."""

    def __init__(
        self,
        output: object = "result",
        tool_calls: list[ToolCallRecord] | None = None,
        cost: CostBreakdown | None = None,
        latency: LatencyBreakdown | None = None,
        success: bool = True,
        error: str | None = None,
        raise_error: Exception | None = None,
        delay_ms: float = 0.0,
    ):
        self.output = output
        self.tool_calls = tool_calls or []
        self.cost = cost or CostBreakdown()
        self.latency = latency or LatencyBreakdown()
        self.success = success
        self.error = error
        self.raise_error = raise_error
        self.delay_ms = delay_ms
        self.call_count = 0
        self.last_scenario: Scenario | None = None

    async def execute(self, scenario: Scenario) -> ExecutionTrace:
        self.call_count += 1
        self.last_scenario = scenario
        if self.delay_ms > 0:
            import asyncio

            await asyncio.sleep(self.delay_ms / 1000.0)
        if self.raise_error is not None:
            raise self.raise_error
        return ExecutionTrace(
            output=self.output,
            tool_calls=self.tool_calls,
            cost=self.cost,
            latency=self.latency,
            error=self.error,
            success=self.success,
        )


@pytest.fixture
def mock_executor() -> MockExecutor:
    return MockExecutor()


@pytest.fixture
def simple_scenario() -> Scenario:
    return Scenario(
        name="test-scenario",
        description="A simple test",
        input_data={"query": "hello"},
        expected_output="result",
        expected_tool_calls=["agent-a", "agent-b"],
    )


@pytest.fixture
def simple_suite(simple_scenario: Scenario) -> EvalSuite:
    return EvalSuite(
        name="test-suite",
        scenarios=[simple_scenario],
    )


@pytest.fixture
def multi_scenario_suite() -> EvalSuite:
    return EvalSuite(
        name="multi-suite",
        scenarios=[
            Scenario(
                name="scenario-1",
                input_data={"x": 1},
                expected_output=10,
                expected_tool_calls=["calc"],
            ),
            Scenario(
                name="scenario-2",
                input_data={"x": 2},
                expected_output=20,
                expected_tool_calls=["calc", "format"],
            ),
            Scenario(
                name="scenario-3",
                input_data={"x": 3},
                expected_output=30,
            ),
        ],
    )
