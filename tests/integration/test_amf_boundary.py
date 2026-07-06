"""Boundary tests: bifrost-eval evaluating REAL agent-mcp-framework pipelines.

These tests cross the integration boundary — they exercise the exact code path
a user follows from the README, against the real framework rather than mocks.
A correct pipeline must grade as correct; a wrong one must grade as wrong; and
dimensions with no data must sit out of the grade rather than score perfect.
"""

from __future__ import annotations

import pytest

amf = pytest.importorskip("agent_mcp_framework")

from bifrost_eval import (  # noqa: E402
    AccuracyMetric,
    CostEfficiencyMetric,
    EvalRunner,
    EvalSuite,
    Scenario,
    ToolCorrectnessMetric,
)
from bifrost_eval.adapters.amf_adapter import AMFAdapter  # noqa: E402


def _make_runner(metrics: list) -> EvalRunner:
    agent = amf.FunctionAgent("doubler", lambda ctx: {"answer": ctx.data["x"] * 2})
    pipeline = amf.SequentialPipeline("test-pipeline", agents=[agent])
    return EvalRunner(executor=AMFAdapter(pipeline), metrics=metrics)


class TestAMFBoundary:
    async def test_correct_pipeline_scores_full_accuracy(self) -> None:
        """The README integration example: a right answer must grade as right."""
        runner = _make_runner([AccuracyMetric()])
        suite = EvalSuite(
            name="amf-correct",
            scenarios=[
                Scenario(name="double", input_data={"x": 21}, expected_output={"answer": 42})
            ],
        )
        result = await runner.run_suite(suite)
        assert result.pass_rate == 1.0
        accuracy = result.outcomes[0].scores[0]
        assert accuracy.value == 1.0

    async def test_wrong_pipeline_scores_zero_accuracy(self) -> None:
        runner = _make_runner([AccuracyMetric()])
        suite = EvalSuite(
            name="amf-wrong",
            scenarios=[
                Scenario(name="double", input_data={"x": 21}, expected_output={"answer": 99})
            ],
        )
        result = await runner.run_suite(suite)
        assert result.pass_rate == 0.0
        assert result.outcomes[0].scores[0].value == 0.0

    async def test_missing_cost_data_is_excluded_not_perfect(self) -> None:
        """AMF reports no cost data; the cost metric must sit out of the grade,
        never inflate it."""
        runner = _make_runner([AccuracyMetric(), CostEfficiencyMetric(budget_usd=0.10)])
        suite = EvalSuite(
            name="amf-cost",
            scenarios=[
                Scenario(name="double", input_data={"x": 21}, expected_output={"answer": 42})
            ],
        )
        result = await runner.run_suite(suite)
        outcome = result.outcomes[0]
        cost_score = next(s for s in outcome.scores if s.name == "cost_efficiency")
        assert cost_score.weight == 0.0
        # The grade is carried entirely by measurable dimensions
        assert outcome.weighted_score == 1.0

    async def test_multi_agent_pipeline_final_output_wins(self) -> None:
        """A sequential pipeline's answer is its final agent's output."""
        first = amf.FunctionAgent("adder", lambda ctx: {"total": ctx.data["x"] + 1})
        second = amf.FunctionAgent("formatter", lambda ctx: "done")
        pipeline = amf.SequentialPipeline("two-step", agents=[first, second])
        runner = EvalRunner(executor=AMFAdapter(pipeline), metrics=[AccuracyMetric()])
        suite = EvalSuite(
            name="amf-two-step",
            scenarios=[Scenario(name="chain", input_data={"x": 1}, expected_output="done")],
        )
        result = await runner.run_suite(suite)
        assert result.outcomes[0].scores[0].value == 1.0

    async def test_agent_sequence_recorded_as_tool_calls(self) -> None:
        first = amf.FunctionAgent("step-one", lambda ctx: {"a": 1})
        second = amf.FunctionAgent("step-two", lambda ctx: {"b": 2})
        pipeline = amf.SequentialPipeline("ordered", agents=[first, second])
        runner = EvalRunner(
            executor=AMFAdapter(pipeline), metrics=[ToolCorrectnessMetric()]
        )
        suite = EvalSuite(
            name="amf-order",
            scenarios=[
                Scenario(
                    name="sequence",
                    input_data={},
                    expected_tool_calls=["step-one", "step-two"],
                )
            ],
        )
        result = await runner.run_suite(suite)
        assert result.outcomes[0].scores[0].value == 1.0
