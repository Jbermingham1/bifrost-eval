"""A/B comparison runner for evaluating different pipeline configurations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from bifrost_eval.core.runner import EvalRunner, PipelineExecutor
from bifrost_eval.core.scorer import Scorer
from bifrost_eval.models.evaluation import EvalResult, EvalSuite  # noqa: TC001

if TYPE_CHECKING:
    from bifrost_eval.core.metrics import Metric


class ComparisonResult(BaseModel):
    """Result of comparing two or more pipeline configurations on the same suite."""

    suite_name: str
    results: dict[str, EvalResult] = Field(default_factory=dict)
    winner: str = ""
    summary: dict[str, Any] = Field(default_factory=dict)

    def determine_winner(self) -> str:
        """Determine which configuration scored highest overall."""
        if not self.results:
            return ""
        best_name = ""
        best_score = -1.0
        for name, result in self.results.items():
            if result.mean_score > best_score:
                best_score = result.mean_score
                best_name = name
        self.winner = best_name
        self.summary = {
            name: {
                "mean_score": r.mean_score,
                "pass_rate": r.pass_rate,
                "total_cost_usd": r.total_cost.total_usd,
                "total_latency_ms": r.total_latency.total_ms,
                "grade": r.grade.value,
            }
            for name, r in self.results.items()
        }
        return best_name


class ComparisonRunner:
    """Run the same evaluation suite against multiple pipeline configurations."""

    def __init__(
        self,
        metrics: list[Metric] | None = None,
        scorer: Scorer | None = None,
    ):
        self.metrics = metrics or []
        self.scorer = scorer or Scorer()

    async def compare(
        self,
        suite: EvalSuite,
        configurations: dict[str, PipelineExecutor],
    ) -> ComparisonResult:
        """Run the suite against each configuration and compare results."""
        comparison = ComparisonResult(suite_name=suite.name)

        for name, executor in configurations.items():
            runner = EvalRunner(
                executor=executor,
                metrics=self.metrics,
                scorer=self.scorer,
            )
            result = await runner.run_suite(suite)
            comparison.results[name] = result

        comparison.determine_winner()
        return comparison
