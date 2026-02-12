"""bifrost-eval: MCP pipeline evaluation toolkit."""

from bifrost_eval.adapters.comparison import ComparisonResult, ComparisonRunner
from bifrost_eval.core.metrics import (
    AccuracyMetric,
    CostEfficiencyMetric,
    LatencyMetric,
    Metric,
    ToolCorrectnessMetric,
)
from bifrost_eval.core.runner import EvalRunner, ExecutionTrace, PipelineExecutor
from bifrost_eval.core.scorer import GradingStrategy, Scorer, ThresholdGrader, WeightedGrader
from bifrost_eval.models.evaluation import (
    CostBreakdown,
    EvalResult,
    EvalScore,
    EvalSuite,
    GradeLevel,
    LatencyBreakdown,
    Scenario,
    ScenarioOutcome,
    ToolCallRecord,
)

__version__ = "0.1.0"

__all__ = [
    "AccuracyMetric",
    "ComparisonResult",
    "ComparisonRunner",
    "CostBreakdown",
    "CostEfficiencyMetric",
    "EvalResult",
    "EvalRunner",
    "EvalScore",
    "EvalSuite",
    "ExecutionTrace",
    "GradeLevel",
    "GradingStrategy",
    "LatencyBreakdown",
    "LatencyMetric",
    "Metric",
    "PipelineExecutor",
    "Scenario",
    "ScenarioOutcome",
    "Scorer",
    "ThresholdGrader",
    "ToolCallRecord",
    "ToolCorrectnessMetric",
    "WeightedGrader",
]
