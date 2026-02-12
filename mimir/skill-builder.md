# Skill Builder — Deepen Your Understanding

## Level 1: Basics

### Q: What's the difference between a metric and a grade?
**A:** A metric measures one specific thing (like accuracy or speed). A grade is the overall verdict after combining all metrics together.

### Q: What happens if an AI agent uses the wrong tools?
**A:** The ToolCorrectnessMetric catches this. It checks three things: (1) were the right tools called, (2) were they called in the right order, (3) were any unnecessary tools called.

### Exercise: Imagine an AI that should search Google, then summarize. Write down what a "perfect" and "failing" scenario would look like.

---

## Level 2: Intermediate

### Q: Why track cost per agent and per tool separately?
**A:** Because you need to know WHERE the money is going. If one agent in a five-agent pipeline costs 80% of the total, you know exactly what to optimize.

### Q: What's the value of A/B comparison testing?
**A:** It lets you make data-driven decisions. Instead of guessing which model or prompt is better, you run the same test suite against both and let the numbers decide.

### Exercise: Think of two ways to build a customer support bot. What metrics would you use to decide between them?

---

## Level 3: Advanced

### Q: Why does bifrost-eval use a "Protocol" for pipeline integration?
**A:** So it works with ANY agent framework, not just ours. You implement one method (`execute`) and the whole evaluation engine works. This is called "programming to an interface, not an implementation."

### Q: How does weighted scoring affect grades?
**A:** Weights let you say "accuracy matters 3x more than speed." A pipeline that's very accurate but slow would score higher than one that's fast but wrong.

### Exercise: Design a custom metric for "hallucination rate" — what would it measure and how would you score it?

---

## Conversation Starters
- "The biggest gap in the AI agent ecosystem is evaluation — everyone builds agents but nobody systematically measures if they work"
- "We treat AI agent evaluation like software testing — define scenarios, run them, check results, automate it"
- "The key insight is evaluating pipelines, not just prompts — a correct tool call sequence matters as much as the final answer"
