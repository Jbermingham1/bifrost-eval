"""Adapter for agent-mcp-framework pipeline evaluation.

Requires the 'amf' optional dependency:
    pip install bifrost-eval[amf]
"""

from __future__ import annotations

import time
from typing import Any, Protocol, cast

from bifrost_eval.core.runner import ExecutionTrace
from bifrost_eval.models.evaluation import (
    CostBreakdown,
    LatencyBreakdown,
    Scenario,
    ToolCallRecord,
)


class _AgentResult(Protocol):
    """Minimal protocol for agent-mcp-framework AgentResult."""

    agent_name: str
    success: bool
    error: str | None
    duration_ms: float


class _PipelineResult(Protocol):
    """Minimal protocol for agent-mcp-framework PipelineResult."""

    success: bool
    outputs: Any
    results: list[_AgentResult]


class _Pipeline(Protocol):
    """Minimal protocol for agent-mcp-framework Pipeline."""

    async def execute(self, ctx: Any) -> _PipelineResult: ...


class AMFAdapter:
    """Adapts an agent-mcp-framework Pipeline for use with bifrost-eval.

    Usage:
        from agent_mcp_framework import SequentialPipeline
        from bifrost_eval.adapters.amf_adapter import AMFAdapter

        pipeline = SequentialPipeline("my-pipeline", agents=[...])
        adapter = AMFAdapter(pipeline)
        runner = EvalRunner(executor=adapter, metrics=[...])
    """

    def __init__(
        self,
        pipeline: _Pipeline,
        context_builder: Any | None = None,
        output_extractor: Any | None = None,
    ) -> None:
        self.pipeline = pipeline
        self._context_builder = context_builder
        self._output_extractor = output_extractor

    async def execute(self, scenario: Scenario) -> ExecutionTrace:
        """Execute the AMF pipeline for the given scenario."""
        try:
            from agent_mcp_framework import AgentContext  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "agent-mcp-framework is required for AMFAdapter. "
                "Install with: pip install bifrost-eval[amf]"
            ) from exc

        # Build context from scenario input
        if self._context_builder is not None:
            ctx: Any = self._context_builder(scenario)
        else:
            ctx = cast("Any", AgentContext(data=scenario.input_data))

        start = time.monotonic()
        result: _PipelineResult = await self.pipeline.execute(ctx)
        elapsed = (time.monotonic() - start) * 1000

        # Extract output
        if self._output_extractor is not None:
            output: Any = self._output_extractor(result, ctx)
        else:
            output = result.outputs

        # Build tool call records from agent results
        tool_calls = _extract_tool_calls(result)

        # Build latency breakdown
        latency = LatencyBreakdown(total_ms=elapsed)
        for agent_result in result.results:
            latency.per_agent[agent_result.agent_name] = agent_result.duration_ms

        return ExecutionTrace(
            output=output,
            tool_calls=tool_calls,
            cost=CostBreakdown(),
            latency=latency,
            error=_first_error(result),
            success=result.success,
        )


def _extract_tool_calls(result: _PipelineResult) -> list[ToolCallRecord]:
    """Extract tool call records from pipeline results."""
    records: list[ToolCallRecord] = []
    for agent_result in result.results:
        records.append(
            ToolCallRecord(
                tool_name=agent_result.agent_name,
                success=agent_result.success,
                error=agent_result.error,
                duration_ms=agent_result.duration_ms,
            )
        )
    return records


def _first_error(result: _PipelineResult) -> str | None:
    """Get the first error from failed results."""
    for r in result.results:
        if not r.success and r.error:
            return r.error
    return None
