# bifrost-eval

[![CI](https://github.com/Jbermingham1/bifrost-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/Jbermingham1/bifrost-eval/actions)
[![PyPI](https://img.shields.io/pypi/v/bifrost-eval)](https://pypi.org/project/bifrost-eval/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/bifrost-eval)](https://pypi.org/project/bifrost-eval/)

**MCP pipeline evaluation toolkit** — grade AI agent workflows on accuracy, cost, and reliability.

## What It Does

bifrost-eval evaluates multi-agent MCP pipelines as complete workflows, not just individual prompts. It answers:

- **Did the pipeline get the right answer?** (accuracy scoring)
- **Did agents use the right tools in the right order?** (tool correctness)
- **How fast was it?** (latency breakdown per agent/tool)
- **How much did it cost?** (cost attribution per agent/tool)
- **How do different configurations compare?** (A/B testing)

## Install

```bash
pip install bifrost-eval
```

With agent-mcp-framework integration:

```bash
pip install bifrost-eval[amf]
```

## Quick Start

```python
import asyncio
from bifrost_eval import (
    AccuracyMetric,
    CostEfficiencyMetric,
    EvalRunner,
    EvalSuite,
    LatencyMetric,
    Scenario,
    ToolCorrectnessMetric,
)

# Define test scenarios
suite = EvalSuite(
    name="my-agent-eval",
    scenarios=[
        Scenario(
            name="basic-query",
            input_data={"query": "What is 2+2?"},
            expected_output=4,
            expected_tool_calls=["calculator"],
        ),
    ],
)

# Implement PipelineExecutor protocol for your agent
class MyExecutor:
    async def execute(self, scenario):
        from bifrost_eval import ExecutionTrace
        # Run your agent pipeline here
        return ExecutionTrace(output=4, success=True)

# Run evaluation
runner = EvalRunner(
    executor=MyExecutor(),
    metrics=[
        AccuracyMetric(weight=2.0),
        ToolCorrectnessMetric(weight=1.0),
        LatencyMetric(target_ms=5000),
        CostEfficiencyMetric(budget_usd=0.10),
    ],
)

result = asyncio.run(runner.run_suite(suite))
print(f"Pass rate: {result.pass_rate:.0%}")
print(f"Grade: {result.grade.value}")
print(f"Total cost: ${result.total_cost.total_usd:.4f}")
```

## A/B Comparison

```python
from bifrost_eval.adapters.comparison import ComparisonRunner

comparator = ComparisonRunner(metrics=[AccuracyMetric(), CostEfficiencyMetric()])
result = await comparator.compare(
    suite,
    {"config-a": executor_a, "config-b": executor_b},
)
print(f"Winner: {result.winner}")
```

## agent-mcp-framework Integration

```python
from agent_mcp_framework import SequentialPipeline
from bifrost_eval.adapters.amf_adapter import AMFAdapter

pipeline = SequentialPipeline("my-pipeline", agents=[...])
adapter = AMFAdapter(pipeline)
runner = EvalRunner(executor=adapter, metrics=[...])
```

## CLI

```bash
# Validate a suite file
bifrost-eval validate suite.json

# Show version
bifrost-eval --version
```

## Metrics

| Metric | What It Measures | Default Weight |
|--------|-----------------|----------------|
| `AccuracyMetric` | Output correctness | 1.0 |
| `ToolCorrectnessMetric` | Right tools, right order | 1.0 |
| `LatencyMetric` | Speed vs target | 1.0 |
| `CostEfficiencyMetric` | Cost vs budget | 1.0 |

## License

MIT
