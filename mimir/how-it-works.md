# How The Inspector Works

## The Recipe (Step by Step)

### Step 1: Write Test Scenarios
Think of these like exam questions for your AI. Each scenario says:
- "Here's the input" (the question)
- "Here's what the answer should be" (the expected result)
- "Here are the tools it should use" (the expected process)

**Example:** "If someone asks 'What is 2+2?', the AI should use the calculator tool and return 4."

### Step 2: Run the Test
The Inspector feeds each scenario to your AI pipeline and watches what happens:
- What answer did it give?
- Which tools did it call?
- How long did it take?
- How much did it cost?

### Step 3: Score Each Dimension
Like grading an essay on multiple criteria:
- **Accuracy** (0-100%): Did it get the right answer?
- **Tool Correctness** (0-100%): Did it use the right tools in the right order?
- **Latency** (0-100%): Was it fast enough vs your target?
- **Cost Efficiency** (0-100%): Was it within budget?

### Step 4: Grade the Result
All scores are combined into a final grade:
- **Excellent** (90%+) — Production ready
- **Good** (75-89%) — Solid, minor improvements possible
- **Acceptable** (60-74%) — Works, but needs optimization
- **Poor** (40-59%) — Significant issues
- **Fail** (<40%) — Broken, don't deploy

### Step 5: Compare Configurations (Optional)
Run the same tests against two different setups and see which one wins. Like A/B testing for AI.

## The Flow

```
Test Scenarios → Run Against AI Pipeline → Collect Metrics → Score → Grade → Report
```

That's it. No magic. Just systematic measurement.
