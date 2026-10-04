"""LangChain tools the agent can call. Each wraps one validation capability."""
import json

from langchain_core.tools import tool

import quality_analyzer
import security_checker
import tester
import validator


@tool
def syntax_tool(code: str, function_name: str = "") -> dict:
    """Check Python syntax (AST + compile) and basic structure."""
    ok, err = validator.check_syntax(code)
    return {"syntax_ok": ok, "syntax_error": err,
            "structure_ok": ok and validator.check_structure(code, function_name)}


@tool
def security_tool(code: str) -> dict:
    """Scan code for dangerous calls, suspicious imports and hardcoded secrets."""
    issues, high = security_checker.scan(code)
    return {"issues": issues, "high": high}


@tool
def quality_tool(code: str) -> dict:
    """Run Ruff lint and Radon complexity metrics."""
    cc, mi = quality_analyzer.complexity(code)
    return {"ruff": quality_analyzer.ruff_issues(code), "cyclomatic": cc, "maintainability": mi}


@tool
def test_tool(code: str, function_name: str, cases_json: str) -> dict:
    """Run reference test cases (JSON list) against the function in a sandboxed subprocess."""
    total, passed, fails = tester.run_tests(code, function_name, json.loads(cases_json))
    return {"total": total, "passed": passed, "failures": fails}


TOOLS = {t.name: t for t in (syntax_tool, security_tool, quality_tool, test_tool)}
