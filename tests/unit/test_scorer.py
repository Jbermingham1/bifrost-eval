"""Tests for scoring and grading strategies."""

from __future__ import annotations

from bifrost_eval.core.scorer import Scorer, ThresholdGrader, WeightedGrader
from bifrost_eval.models.evaluation import EvalScore, GradeLevel, ScenarioOutcome


class TestThresholdGrader:
    def test_excellent(self) -> None:
        grader = ThresholdGrader()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.95)],
        )
        assert grader.grade(outcome) == GradeLevel.EXCELLENT

    def test_good(self) -> None:
        grader = ThresholdGrader()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.8)],
        )
        assert grader.grade(outcome) == GradeLevel.GOOD

    def test_acceptable(self) -> None:
        grader = ThresholdGrader()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.65)],
        )
        assert grader.grade(outcome) == GradeLevel.ACCEPTABLE

    def test_poor(self) -> None:
        grader = ThresholdGrader()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.45)],
        )
        assert grader.grade(outcome) == GradeLevel.POOR

    def test_fail(self) -> None:
        grader = ThresholdGrader()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.2)],
        )
        assert grader.grade(outcome) == GradeLevel.FAIL

    def test_custom_thresholds(self) -> None:
        grader = ThresholdGrader(excellent=0.95, good=0.85, acceptable=0.7, poor=0.5)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.8)],
        )
        assert grader.grade(outcome) == GradeLevel.ACCEPTABLE

    def test_boundary_excellent(self) -> None:
        grader = ThresholdGrader()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.9)],
        )
        assert grader.grade(outcome) == GradeLevel.EXCELLENT

    def test_boundary_poor(self) -> None:
        grader = ThresholdGrader()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.4)],
        )
        assert grader.grade(outcome) == GradeLevel.POOR


class TestWeightedGrader:
    def test_basic_grading(self) -> None:
        grader = WeightedGrader()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.95)],
        )
        assert grader.grade(outcome) == GradeLevel.EXCELLENT

    def test_required_score_fail(self) -> None:
        grader = WeightedGrader(required_scores={"accuracy": 0.8})
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="accuracy", value=0.5)],
        )
        assert grader.grade(outcome) == GradeLevel.FAIL

    def test_required_score_pass(self) -> None:
        grader = WeightedGrader(required_scores={"accuracy": 0.8})
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="accuracy", value=0.9)],
        )
        assert grader.grade(outcome) == GradeLevel.EXCELLENT

    def test_required_score_missing(self) -> None:
        grader = WeightedGrader(required_scores={"accuracy": 0.8})
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="speed", value=0.95)],
        )
        # Should not fail if the required score dimension isn't present
        assert grader.grade(outcome) == GradeLevel.EXCELLENT

    def test_custom_min_pass(self) -> None:
        grader = WeightedGrader(min_pass_score=0.7)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.65)],
        )
        assert grader.grade(outcome) == GradeLevel.POOR


class TestScorer:
    def test_apply_grade_passing(self) -> None:
        scorer = Scorer()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=False,
            scores=[EvalScore(name="acc", value=0.95)],
        )
        scorer.apply_grade(outcome)
        assert outcome.passed is True
        assert outcome.grade == GradeLevel.EXCELLENT

    def test_apply_grade_failing(self) -> None:
        scorer = Scorer()
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.2)],
        )
        scorer.apply_grade(outcome)
        assert outcome.passed is False
        assert outcome.grade == GradeLevel.FAIL

    def test_custom_grader(self) -> None:
        grader = ThresholdGrader(excellent=0.99)
        scorer = Scorer(grader=grader)
        outcome = ScenarioOutcome(
            scenario_name="test",
            passed=True,
            scores=[EvalScore(name="acc", value=0.95)],
        )
        scorer.apply_grade(outcome)
        assert outcome.grade == GradeLevel.GOOD
