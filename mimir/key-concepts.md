# Key Concepts (Translated)

## 1. Evaluation Suite
**Normal words:** A collection of test exams for your AI.
**Tech:** An `EvalSuite` contains multiple `Scenario` objects that test different capabilities.

## 2. Scenario
**Normal words:** One specific exam question with the correct answer.
**Tech:** Input data + expected output + expected tool usage + timeout.

## 3. Metric
**Normal words:** One measuring stick (like "speed" or "accuracy").
**Tech:** A class that takes a result and produces a score from 0 to 1.

## 4. Score
**Normal words:** The AI's grade on one measuring stick.
**Tech:** A number from 0.0 to 1.0, with a weight that says how important this dimension is.

## 5. Grade Level
**Normal words:** The overall letter grade (Excellent/Good/Acceptable/Poor/Fail).
**Tech:** Derived from weighted average of all scores using a `GradingStrategy`.

## 6. Pipeline Executor
**Normal words:** The connector between The Inspector and your AI system.
**Tech:** An interface (protocol) that takes a scenario and returns a trace of what happened.

## 7. Execution Trace
**Normal words:** The complete recording of what the AI did during one test.
**Tech:** Output + tool calls + cost data + timing data + any errors.

## 8. A/B Comparison
**Normal words:** Running the same exams on two different AI setups to see which is better.
**Tech:** `ComparisonRunner` executes the same suite against multiple executors and picks the winner.

## 9. Cost Attribution
**Normal words:** Breaking down how much each part of the AI costs (per agent, per tool).
**Tech:** `CostBreakdown` with per-agent and per-tool USD tracking.

## 10. Tool Correctness
**Normal words:** Did the AI use the right tools in the right order?
**Tech:** Measures presence (right tools called), order (correct sequence), and extras (unnecessary calls).
