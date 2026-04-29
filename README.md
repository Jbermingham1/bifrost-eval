# bifrost-eval

[![CI](https://github.com/Jbermingham1/bifrost-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/Jbermingham1/bifrost-eval/actions)
[![PyPI](https://img.shields.io/pypi/v/bifrost-eval)](https://pypi.org/project/bifrost-eval/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/bifrost-eval)](https://pypi.org/project/bifrost-eval/)
[![Type Checked: pyright strict](https://img.shields.io/badge/pyright-strict-brightgreen)](https://github.com/microsoft/pyright)

**MCP pipeline evaluation toolkit** — grade AI agent workflows on accuracy, cost, and reliability.

## Why

Most LLM evaluation tooling grades a single prompt against a single response. Multi-agent pipelines aren't single prompts — they're orchestrations. A "correct" answer reached by the wrong tool in the wrong order is still a regression. A correct answer that took 30 seconds and cost $0.40 isn't shippable. A correct answer 80% of the time isn't a product.

`bifrost-eval` grades the **whole workflow** as a unit. Did it get the right answer, with the right tools, in the right order, fast enough, cheap enough? It produces a single graded report so a change to the pipeline either improves the score or it doesn't.

## Architecture

```
   scenarios ─▶  EvalRunner  ─▶  PipelineExecutor (your code)  ─▶  ExecutionTrace
                     │                                                    │
                     │                       ┌────────────────────────────┘
                     ▼                       ▼
                  Metrics                 outcomes
            ┌──────────────┐
            │ Accuracy     │
            │ ToolCorrect. │  ─▶  weighted score  ─▶  threshold/weighted grade
            │ Latency      │
            │ Cost         │
            └──────────────┘
```

## What It Does

bifrost-eval evaluates multi-agent MCP pipelines as complete workflows, not just individual prompts. It answers:

- **Did the pipeline get the right answer?** (accuracy scoring)
- **Did agents use the right tools in the right order?** (tool correctness via Longest-Common-Subsequence)
- **How fast was it?** (latency breakdown per agent/tool, p50/p95/p99 percentiles)
- **How much did it cost?** (cost attribution per agent/tool)
- **How do different configurations compare?** (A/B testing with statistical winner)

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

## When to use this (and when not to)

| Use `bifrost-eval` when… | Reach for something else when… |
|---|---|
| You have a multi-agent or multi-tool pipeline you need to grade as a single workflow | You only need to grade single-prompt single-response interactions (use `lm-eval-harness` or task-specific benchmarks) |
| You want statistical A/B comparisons between pipeline configurations | You want a managed eval-as-a-service with a UI (use LangSmith, Weights & Biases) |
| You want a small library you can drop into a Python codebase | You want a no-code eval product |
| You want strict type-checking and property-based-tested metric implementations | You want a thousand pre-built benchmarks out of the box |

## Composes with

- [`bifrost-rag`](https://github.com/Jbermingham1/bifrost-rag) — RAG pipeline + retrieval-quality metrics (Precision@K, Recall@K, F1, MRR). Use together to grade RAG-retrieval-then-agent workflows end-to-end.
- [`bifrost-monitor`](https://github.com/Jbermingham1/bifrost-monitor) — runtime observability for AI agents. Use together to evaluate offline + observe online.
- [`agent-mcp-framework`](https://github.com/Jbermingham1/agent-mcp-framework) — multi-agent MCP pipeline framework. `bifrost-eval` ships a first-class adapter (`bifrost_eval.adapters.amf_adapter`).

## Engineering bar

- **pyright strict** type checking (zero ignores in metric implementations)
- **80% test coverage gate** enforced in CI
- **Hypothesis property-based fuzzing** on metrics — score outputs bounded in `[0.0, 1.0]` over arbitrary inputs
- **Minimal runtime dependencies**: `pydantic` only
- **MIT licensed**

## License

MIT
