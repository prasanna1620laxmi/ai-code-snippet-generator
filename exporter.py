"""Export results as JSON, .py and a pytest file."""
import json

from models import GenerationResult


def to_json(result: GenerationResult) -> str:
    s = result.snippet
    return json.dumps({
        "requirement": result.spec.requirement,
        "intent": result.spec.category,
        "language": result.spec.language,
        "generated_code": s.code if s else None,
        "complexity": s.complexity if s else None,
        "validation_status": result.validation.state,
        "assumptions": result.spec.assumptions,
        "explanation": s.explanation if s else None,
        "repair_attempts": result.repair_attempts,
    }, indent=2)


def to_python(result: GenerationResult) -> str:
    return (result.snippet.code if result.snippet else "")


def to_pytest(result: GenerationResult, module_name: str = "snippet") -> str:
    s = result.snippet
    if not s or not s.test_cases:
        return "# No reference test cases were generated.\n"
    lines = ["import pytest", f"from {module_name} import {s.function_name}", ""]
    params = ",\n    ".join(f"({c.args!r}, {c.kwargs!r}, {c.expected!r})" for c in s.test_cases)
    lines += [f"@pytest.mark.parametrize('args,kwargs,expected', [\n    {params}\n])",
              "def test_generated(args, kwargs, expected):",
              f"    assert {s.function_name}(*args, **kwargs) == expected", ""]
    return "\n".join(lines)
