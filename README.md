# AI Code Snippet Generator (TCS Technology Day)

Natural-language requirement -> validated, executable Python snippet.
Stack: **Streamlit · LangChain · Google Gemini (free tier) · TensorFlow · Agentic AI · Pydantic · AST · Ruff · Radon · Pytest · SQLite**

## Where each required technology is used
| Technology | Role |
|---|---|
| Generative AI (Gemini, free AI Studio key) | `code_generator.py` - generates code, explanation, complexity, tests as JSON |
| LangChain | Gemini chat model wrapper (`langchain-google-genai`), message handling, and `@tool` definitions in `tools.py` |
| Agentic AI | `agent.py` - single agent: understand -> generate -> call tools -> review -> auto-repair loop -> explain -> return, with a visible trace |
| TensorFlow | `intent_classifier.py` - Keras text classifier (7 categories) trained on `data/synthetic_examples.json` |

## Setup (Python 3.10-3.12; TensorFlow does not support newer versions yet)
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # paste your free Gemini key
python scripts/build_dataset.py                        # optional: regenerate training data
python intent_classifier.py                            # optional: pre-train the TF model
streamlit run app.py
```
Free key: https://aistudio.google.com/apikey . Free-tier model names and limits change; if `gemini-2.5-flash`
is unavailable set `GEMINI_MODEL` in `.env` to another free model.

## Run tests / evaluation
```bash
pytest -q                          # unit tests (no API key needed; agent test uses a fake generator)
python evaluation/evaluate.py      # runs 8 reference problems through Gemini; prints the metrics table
uvicorn api:app --reload           # optional FastAPI endpoint: POST /generate
```

## Pipeline
`Requirement -> validate/normalise -> TF intent -> Gemini (LangChain) -> syntax/structure (AST) -> security scan -> Ruff + Radon -> Pytest-style reference cases (sandboxed subprocess) -> repair loop (max N) -> final state -> export`

Validation states: Passed / Passed with Warnings / Repair Required / Rejected (matches the problem statement).
Code flagged high-risk is never executed by the test runner.

## Notes
- Generated code is only run in a separate Python subprocess with a timeout; it is not a hardened sandbox - run on a trusted dev machine.
- The model's own test cases are used during repair; `evaluation/evaluate.py` uses independent reference tests.
