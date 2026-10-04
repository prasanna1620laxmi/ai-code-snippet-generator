# Approach

**Problem:** developers lose time turning textual requirements into boilerplate code, with inconsistent quality.
**Solution:** a zero-cost, single-agent GenAI system that converts a requirement into validated Python.

1. **Input & preprocessing** - normalise text, reject empty/ambiguous input, extract action, entity, inputs, outputs,
   constraints into a Pydantic `RequirementSpec`; record assumptions.
2. **Understanding (TensorFlow)** - Keras classifier maps requirement to Functions / Algorithms / APIs / Classes / CRUD /
   Data Processing / Automation; the category steers the prompt.
3. **Generation (Gemini + LangChain)** - role-based, few-shot prompt, fixed JSON schema (code, explanation, complexity,
   assumptions, test cases).
4. **Agentic validation** - the agent calls four LangChain tools: syntax (AST+compile), security (AST scan), quality
   (Ruff+Radon), tests (subprocess runner). Failures are fed back to Gemini for up to N repairs.
5. **Output** - code, explanation, status, assumptions, warnings, complexity; download .py / .json / pytest file;
   history in SQLite.
6. **Evaluation** - `evaluation/evaluate.py` reports functional correctness (>=80%), syntax accuracy (>=95%), structural
   completeness (>=95%), alignment, latency (<15s).

Demo script: prime check -> factorial (recursion) -> a deliberately risky requirement ("run a shell command from user
input") to show the Rejected state -> History tab -> downloads.
