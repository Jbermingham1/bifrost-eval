"""Evaluation metrics for MCP pipeline assessment."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, cast

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

    def _excluded(self, reason: str) -> EvalScore:
        """A score that sits out of the grade because the dimension can't be measured.

        Weight 0.0 removes it from the weighted average — a dimension with no data
        must never count as a result, perfect or otherwise.
        """
        return EvalScore(name=self.name, value=0.0, weight=0.0, details=f"Excluded: {reason}")


class AccuracyMetric(Metric):
    """Measures whether the actual output matches expected output.

    Uses exact match by default. Supports custom comparators.
    Excluded from the grade when the scenario defines no expected output.
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
            return self._excluded("no expected output defined")

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
    - Presence: were all expected tools called? (weight 0.6)
    - Order: were they called in the right sequence? (weight 0.4, LCS ratio)
    - Extras: unexpected tool calls apply a penalty factor

    Order checking is on by default; pass ``check_order=False`` to score
    presence only. Excluded from the grade when the scenario defines no
    expected tool calls.
    """

    def __init__(self, weight: float = 1.0, check_order: bool = True):
        super().__init__("tool_correctness", weight)
        self.check_order = check_order

    def score(self, outcome: ScenarioOutcome, expected: Any | None = None) -> EvalScore:
        if expected is None:
            return self._excluded("no expected tool calls defined")

        raw = cast("list[str]", expected) if isinstance(expected, list) else list(expected)
        expected_tools: list[str] = raw
        actual_tools = outcome.tool_call_names

        if not expected_tools:
            return self._excluded("no expected tool calls defined")

        # Presence score: what fraction of expected tools were called?
        called_set = set(actual_tools)
        expected_set = set(expected_tools)
        presence = len(called_set & expected_set) / len(expected_set)

        # Order score: longest common subsequence ratio
        if self.check_order:
            order_score = _lcs_ratio(expected_tools, actual_tools)
            base = presence * 0.6 + order_score * 0.4
        else:
            order_score = None
            base = presence

        # Penalty for extra unexpected tools
        extras = called_set - expected_set
        extra_penalty = len(extras) / max(len(actual_tools), 1)

        value = max(0.0, min(1.0, base * (1.0 - extra_penalty * 0.2)))
        order_detail = f"{order_score:.2f}" if order_score is not None else "not checked"
        details = (
            f"Presence: {presence:.2f}, Order: {order_detail}, "
            f"Extras: {len(extras)}, Expected: {expected_tools}, Actual: {actual_tools}"
        )
        return EvalScore(name=self.name, value=value, weight=self.weight, details=details)


class LatencyMetric(Metric):
    """Scores based on how fast the pipeline completed vs a target.

    Excluded from the grade when no latency was recorded.
    """

    def __init__(self, target_ms: float = 5000.0, weight: float = 1.0):
        super().__init__("latency", weight)
        self.target_ms = target_ms

    def score(self, outcome: ScenarioOutcome, expected: Any | None = None) -> EvalScore:
        actual = outcome.latency.total_ms
        if actual <= 0:
            return self._excluded("no latency data recorded")

        value = min(1.0, self.target_ms / actual)
        return EvalScore(
            name=self.name,
            value=value,
            weight=self.weight,
            details=f"Target: {self.target_ms}ms, Actual: {actual:.1f}ms",
        )


class CostEfficiencyMetric(Metric):
    """Scores based on cost vs a budget target.

    Excluded from the grade when no cost was recorded — a pipeline that
    reports nothing must not be graded as free.
    """

    def __init__(self, budget_usd: float = 0.10, weight: float = 1.0):
        super().__init__("cost_efficiency", weight)
        self.budget_usd = budget_usd

    def score(self, outcome: ScenarioOutcome, expected: Any | None = None) -> EvalScore:
        actual = outcome.cost.total_usd
        if actual <= 0:
            return self._excluded("no cost data recorded")

        value = min(1.0, self.budget_usd / actual)
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
