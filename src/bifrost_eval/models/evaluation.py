"""Core evaluation data models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GradeLevel(StrEnum):
    """Grade levels for evaluation outcomes."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAIL = "fail"


class ToolCallRecord(BaseModel):
    """Record of a single tool/MCP call during evaluation."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    success: bool = True
    error: str | None = None
    duration_ms: float = 0.0
    token_count: int = 0
    cost_usd: float = 0.0


class CostBreakdown(BaseModel):
    """Cost attribution for an evaluation run."""

    total_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    per_agent: dict[str, float] = Field(default_factory=dict)
    per_tool: dict[str, float] = Field(default_factory=dict)


class LatencyBreakdown(BaseModel):
    """Latency attribution for an evaluation run."""

    total_ms: float = 0.0
    per_agent: dict[str, float] = Field(default_factory=dict)
    per_tool: dict[str, float] = Field(default_factory=dict)
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0


class EvalScore(BaseModel):
    """A single scored dimension of an evaluation."""

    name: str
    value: float = Field(ge=0.0, le=1.0)
    weight: float = Field(default=1.0, ge=0.0)
    details: str = ""


class Scenario(BaseModel):
    """A test scenario for evaluation."""

    name: str
    description: str = ""
    input_data: dict[str, Any] = Field(default_factory=dict)
    expected_output: Any = None
    expected_tool_calls: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    timeout_ms: float = 30000.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScenarioOutcome(BaseModel):
    """Result of running a single scenario."""

    scenario_name: str
    passed: bool
    scores: list[EvalScore] = Field(default_factory=lambda: list[EvalScore]())
    actual_output: Any = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=lambda: list[ToolCallRecord]())
    cost: CostBreakdown = Field(default_factory=CostBreakdown)
    latency: LatencyBreakdown = Field(default_factory=LatencyBreakdown)
    error: str | None = None
    grade: GradeLevel = GradeLevel.FAIL

    @property
    def weighted_score(self) -> float:
        """Calculate weighted average score across all dimensions."""
        if not self.scores:
            return 0.0
        total_weight = sum(s.weight for s in self.scores)
        if total_weight == 0.0:
            return 0.0
        return sum(s.value * s.weight for s in self.scores) / total_weight

    @property
    def tool_call_names(self) -> list[str]:
        """Get list of tool names called in order."""
        return [tc.tool_name for tc in self.tool_calls]


class EvalResult(BaseModel):
    """Aggregated result from an entire evaluation suite run."""

    suite_name: str
    outcomes: list[ScenarioOutcome] = Field(default_factory=lambda: list[ScenarioOutcome]())
    total_cost: CostBreakdown = Field(default_factory=CostBreakdown)
    total_latency: LatencyBreakdown = Field(default_factory=LatencyBreakdown)
    run_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        """Fraction of scenarios that passed."""
        if not self.outcomes:
            return 0.0
        return sum(1 for o in self.outcomes if o.passed) / len(self.outcomes)

    @property
    def mean_score(self) -> float:
        """Mean weighted score across all outcomes."""
        if not self.outcomes:
            return 0.0
        return sum(o.weighted_score for o in self.outcomes) / len(self.outcomes)

    @property
    def grade(self) -> GradeLevel:
        """Overall grade based on mean score."""
        score = self.mean_score
        if score >= 0.9:
            return GradeLevel.EXCELLENT
        if score >= 0.75:
            return GradeLevel.GOOD
        if score >= 0.6:
            return GradeLevel.ACCEPTABLE
        if score >= 0.4:
            return GradeLevel.POOR
        return GradeLevel.FAIL

    @property
    def passed_count(self) -> int:
        return sum(1 for o in self.outcomes if o.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for o in self.outcomes if not o.passed)


class EvalSuite(BaseModel):
    """A collection of scenarios for evaluation."""

    name: str
    description: str = ""
    scenarios: list[Scenario] = Field(default_factory=lambda: list[Scenario]())
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
