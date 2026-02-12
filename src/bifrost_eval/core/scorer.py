"""Scoring and grading strategies for evaluation outcomes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from bifrost_eval.models.evaluation import GradeLevel, ScenarioOutcome


class GradingStrategy(ABC):
    """Base class for grading strategies."""

    @abstractmethod
    def grade(self, outcome: ScenarioOutcome) -> GradeLevel:
        """Assign a grade to a scenario outcome."""
        ...


class ThresholdGrader(GradingStrategy):
    """Grade based on configurable score thresholds."""

    def __init__(
        self,
        excellent: float = 0.9,
        good: float = 0.75,
        acceptable: float = 0.6,
        poor: float = 0.4,
    ):
        self.excellent = excellent
        self.good = good
        self.acceptable = acceptable
        self.poor = poor

    def grade(self, outcome: ScenarioOutcome) -> GradeLevel:
        score = outcome.weighted_score
        if score >= self.excellent:
            return GradeLevel.EXCELLENT
        if score >= self.good:
            return GradeLevel.GOOD
        if score >= self.acceptable:
            return GradeLevel.ACCEPTABLE
        if score >= self.poor:
            return GradeLevel.POOR
        return GradeLevel.FAIL


class WeightedGrader(GradingStrategy):
    """Grade based on weighted combination of specific score dimensions."""

    def __init__(
        self,
        required_scores: dict[str, float] | None = None,
        min_pass_score: float = 0.6,
    ):
        self.required_scores = required_scores or {}
        self.min_pass_score = min_pass_score

    def grade(self, outcome: ScenarioOutcome) -> GradeLevel:
        score_map = {s.name: s.value for s in outcome.scores}

        # Check required minimums
        for name, minimum in self.required_scores.items():
            if name in score_map and score_map[name] < minimum:
                return GradeLevel.FAIL

        score = outcome.weighted_score
        if score >= 0.9:
            return GradeLevel.EXCELLENT
        if score >= 0.75:
            return GradeLevel.GOOD
        if score >= self.min_pass_score:
            return GradeLevel.ACCEPTABLE
        if score >= 0.4:
            return GradeLevel.POOR
        return GradeLevel.FAIL


class Scorer:
    """Combines metrics and grading to produce scored outcomes."""

    def __init__(
        self,
        grader: GradingStrategy | None = None,
    ):
        self.grader = grader or ThresholdGrader()

    def apply_grade(self, outcome: ScenarioOutcome) -> ScenarioOutcome:
        """Apply grading to an outcome, modifying it in place."""
        outcome.grade = self.grader.grade(outcome)
        outcome.passed = outcome.grade in (
            GradeLevel.EXCELLENT,
            GradeLevel.GOOD,
            GradeLevel.ACCEPTABLE,
        )
        return outcome
