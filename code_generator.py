"""Generative AI layer: LangChain + Google Gemini (free tier via AI Studio key)."""
import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

from models import GeneratedSnippet, RequirementSpec

SYSTEM_PROMPT = """You are a Senior Python Software Engineer.
Convert the requirement into complete, executable Python.
Rules:
- Follow PEP 8, use meaningful names, type hints and a concise docstring.
- Handle stated edge cases and invalid input with clear exceptions.
- Use only the standard library unless the requirement names a library.
- No eval/exec/os.system, no hardcoded credentials, no placeholder (pass/TODO) logic.
- List every assumption you make in "assumptions".
- Provide 3-6 test_cases for the main function as JSON-serialisable data.
Return ONLY valid JSON (no markdown fences) with exactly these keys:
{"function_name": str, "imports": [str], "code": str, "explanation": str,
 "complexity": str, "assumptions": [str],
 "test_cases": [{"args": [..], "kwargs": {}, "expected": ..}]}
Omit test_cases (use []) for classes, APIs, file or database code that cannot be unit-tested simply."""

FEW_SHOT = """Example requirement: Create a function to check whether a number is prime.
Example output: {"function_name": "is_prime", "imports": [], "code": "def is_prime(number: int) -> bool:\\n    \\"\\"\\"Return True when number is prime.\\"\\"\\"\\n    if number <= 1:\\n        return False\\n    for d in range(2, int(number ** 0.5) + 1):\\n        if number % d == 0:\\n            return False\\n    return True\\n", "explanation": "Rejects values <= 1 and checks divisors up to sqrt(n).", "complexity": "O(sqrt(n))", "assumptions": [], "test_cases": [{"args": [2], "expected": true}, {"args": [1], "expected": false}, {"args": [15], "expected": false}, {"args": [97], "expected": true}]}"""


def extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON.")
    return json.loads(text[start:end + 1])


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)


class CodeGenerator:
    def __init__(self, api_key: str | None = None, model: str | None = None, temperature: float = 0.2):
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("Set GEMINI_API_KEY (free key from https://aistudio.google.com/apikey).")
        self.llm = ChatGoogleGenerativeAI(
            model=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            google_api_key=key, temperature=temperature)

    def _build_prompt(self, spec: RequirementSpec, feedback: str | None, previous_code: str | None) -> str:
        p = (f"{FEW_SHOT}\n\nRequirement: {spec.requirement}\nLanguage: {spec.language}\n"
             f"Category: {spec.category}\nAction: {spec.action}\nEntity: {spec.entity}\n"
             f"Inputs: {spec.inputs}\nOutputs: {spec.outputs}\nConstraints: {spec.constraints}\n")
        if feedback:
            p += (f"\nYour previous attempt failed validation.\nPrevious code:\n{previous_code}\n"
                  f"Problems:\n{feedback}\nFix every problem and return the full JSON again.")
        return p

    def generate(self, spec: RequirementSpec, feedback: str | None = None,
                 previous_code: str | None = None) -> GeneratedSnippet:
        msgs = [SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=self._build_prompt(spec, feedback, previous_code))]
        raw = _content_to_text(self.llm.invoke(msgs).content)
        return GeneratedSnippet(**extract_json(raw))
