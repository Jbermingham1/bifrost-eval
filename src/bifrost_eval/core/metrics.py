"""Evaluation metrics for MCP pipeline assessment."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from bifrost_eval.models.evaluation import EvalScore, ScenarioOutcome


class Metric(ABC):
    """Base class for evaluation metrics."""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight

    @abstractmethod
    def score(self, outcome: ScenarioOutcome, expected: Any | None = None) -> EvalScore:
        """Calculate a score for the given outcome."""
        ...


class AccuracyMetric(Metric):
    """Measures whether the actual output matches expected output.

    Uses exact match by default. Supports custom comparators.
    """

    def __init__(
        self,
        weight: float = 1.0,
        comparator: Any | None = None,
    ):
        super().__init__("accuracy", weight)
        self._comparator = comparator

    def score(self, outcome: ScenarioOutcome, expected: Any | None = None) -> EvalScore:
        if expected is None:
            return EvalScore(
                name=self.name, value=1.0, weight=self.weight,
                details="No expected output; skipped",
            )

        if self._comparator is not None:
            match = bool(self._comparator(outcome.actual_output, expected))
        else:
            match = outcome.actual_output == expected

        return EvalScore(
            name=self.name,
            value=1.0 if match else 0.0,
            weight=self.weight,
            details=f"Match: {match}",
        )


class ToolCorrectnessMetric(Metric):
    """Measures whether the correct tools were called in the expected order.

    Scores based on:
    - Presence: were all expected tools called?
    - Order: were they called in the right sequence?
    - Extras: were unexpected tools called?
    """

    def __init__(self, weight: float = 1.0, strict_order: bool = False):
        super().__init__("tool_correctness", weight)
        self.strict_order = strict_order

    def score(self, outcome: ScenarioOutcome, expected: Any | None = None) -> EvalScore:
        if expected is None:
            return EvalScore(
                name=self.name, value=1.0, weight=self.weight, details="No expected tools; skipped"
            )

        expected_tools: list[str] = list(expected) if not isinstance(expected, list) else expected
        actual_tools = outcome.tool_call_names

        if not expected_tools:
            return EvalScore(
                name=self.name, value=1.0, weight=self.weight, details="Empty expected tools"
            )

        # Presence score: what fraction of expected tools were called?
        called_set = set(actual_tools)
        expected_set = set(expected_tools)
        presence = len(called_set & expected_set) / len(expected_set) if expected_set else 1.0

        # Order score: longest common subsequence ratio
        if self.strict_order and expected_tools:
            order_score = _lcs_ratio(expected_tools, actual_tools)
        else:
            order_score = 1.0

        # Penalty for extra unexpected tools
        extras = called_set - expected_set
        extra_penalty = len(extras) / max(len(actual_tools), 1)

        raw = (presence * 0.5 + order_score * 0.3) * (1.0 - extra_penalty * 0.2)
        value = max(0.0, min(1.0, raw))
        details = (
            f"Presence: {presence:.2f}, Order: {order_score:.2f}, "
            f"Extras: {len(extras)}, Expected: {expected_tools}, Actual: {actual_tools}"
        )
        return EvalScore(name=self.name, value=value, weight=self.weight, details=details)


class LatencyMetric(Metric):
    """Scores based on how fast the pipeline completed vs a target."""

    def __init__(self, target_ms: float = 5000.0, weight: float = 1.0):
        super().__init__("latency", weight)
        self.target_ms = target_ms

    def score(self, outcome: ScenarioOutcome, expected: Any | None = None) -> EvalScore:
        actual = outcome.latency.total_ms
        if actual <= 0:
            return EvalScore(
                name=self.name, value=1.0, weight=self.weight,
                details="No latency data",
            )

        ratio = self.target_ms / actual if actual > 0 else 1.0
        value = min(1.0, ratio)
        return EvalScore(
            name=self.name,
            value=value,
            weight=self.weight,
            details=f"Target: {self.target_ms}ms, Actual: {actual:.1f}ms",
        )


class CostEfficiencyMetric(Metric):
    """Scores based on cost vs a budget target."""

    def __init__(self, budget_usd: float = 0.10, weight: float = 1.0):
        super().__init__("cost_efficiency", weight)
        self.budget_usd = budget_usd

    def score(self, outcome: ScenarioOutcome, expected: Any | None = None) -> EvalScore:
        actual = outcome.cost.total_usd
        if actual <= 0:
            return EvalScore(
                name=self.name, value=1.0, weight=self.weight, details="No cost data"
            )

        ratio = self.budget_usd / actual if actual > 0 else 1.0
        value = min(1.0, ratio)
        return EvalScore(
            name=self.name,
            value=value,
            weight=self.weight,
            details=f"Budget: ${self.budget_usd:.4f}, Actual: ${actual:.4f}",
        )


def _lcs_ratio(expected: list[str], actual: list[str]) -> float:
    """Longest common subsequence ratio between two tool call sequences."""
    if not expected or not actual:
        return 0.0

    m, n = len(expected), len(actual)
    dp: list[list[int]] = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if expected[i - 1] == actual[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_len = dp[m][n]
    return lcs_len / m
