# What You Can Say (Interview Talking Points)

## The 30-Second Elevator Pitch
"I built an evaluation framework that grades AI agent pipelines on accuracy, cost, and reliability. Instead of just eyeballing if an AI works, it runs systematic tests and produces scorecards — like unit tests for human code, but for multi-agent workflows."

## When Asked "What Does This Do?"
"Most teams deploying AI agents have no systematic way to measure quality. They look at output and say 'looks fine.' bifrost-eval changes that. You define test scenarios with expected outputs, run them against your pipeline, and get scored results across accuracy, tool usage, latency, and cost. You can also A/B test different configurations to find the best setup."

## When Asked "How Is This Different From DeepEval?"
"DeepEval is great for testing individual LLM outputs — like grading one essay. bifrost-eval evaluates entire multi-agent pipelines — like grading the whole exam process from start to finish. We focus on pipeline-level metrics that DeepEval doesn't: per-agent cost attribution, tool call sequence correctness, and comparative configuration testing. They're complementary tools."

## When Asked "Why Did You Build This?"
"Working with multi-agent MCP pipelines, I kept running into the same problem: how do you know if your pipeline is actually performing well? Is it using the right tools? Is it cost-efficient? I couldn't find a tool that evaluated the whole pipeline holistically, so I built one."

## When Asked About Technical Decisions
- "Full type safety with Pydantic models and pyright strict mode — catches bugs before they reach production"
- "Pluggable metrics system — you can add custom scoring dimensions without modifying core code"
- "Protocol-based integration — any pipeline framework can plug in by implementing one simple interface"
- "111 tests at 90% coverage — CI blocks the build if coverage drops below 80%"

## Key Numbers
- 111 tests, 90% coverage
- 4 built-in metrics (accuracy, tool correctness, latency, cost)
- A/B comparison runner for configuration testing
- Native integration with agent-mcp-framework
- Full CI/CD with lint, type check, test, security scan, build, publish
