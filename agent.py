"""Single-agent orchestrator (agentic AI).

Plan -> Generate -> call validation tools -> if problems, feed them back to the LLM
and repair (bounded loop) -> classify final state. The trace records every decision.
"""
import json
import time

import intent_classifier
import requirement_processor
from models import GenerationResult, GeneratedSnippet, ValidationReport
from tools import TOOLS


class CodeAgent:
    def __init__(self, generator, max_repairs: int = 2, use_tensorflow: bool = True):
        self.generator = generator
        self.max_repairs = max_repairs
        self.use_tensorflow = use_tensorflow

    # -- tool-using review step ------------------------------------------------
    def review(self, snippet: GeneratedSnippet) -> ValidationReport:
        r = ValidationReport()
        s = TOOLS["syntax_tool"].invoke({"code": snippet.code, "function_name": snippet.function_name})
        r.syntax_ok, r.syntax_error, r.structure_ok = s["syntax_ok"], s["syntax_error"], s["structure_ok"]
        if not r.syntax_ok:
            r.state = "Repair Required"
            return r
        sec = TOOLS["security_tool"].invoke({"code": snippet.code})
        r.security_issues, r.high_severity = sec["issues"], sec["high"]
        q = TOOLS["quality_tool"].invoke({"code": snippet.code})
        r.ruff_issues, r.cyclomatic, r.maintainability = q["ruff"], q["cyclomatic"], q["maintainability"]
        if snippet.test_cases and not r.high_severity:  # never execute code flagged as unsafe
            cases = json.dumps([c.model_dump() for c in snippet.test_cases])
            t = TOOLS["test_tool"].invoke({"code": snippet.code, "function_name": snippet.function_name,
                                           "cases_json": cases})
            r.tests_total, r.tests_passed, r.test_failures = t["total"], t["passed"], t["failures"]
        return r

    @staticmethod
    def _final_state(r: ValidationReport) -> str:
        if r.high_severity:
            return "Rejected"
        if not r.syntax_ok or not r.structure_ok or r.tests_passed < r.tests_total:
            return "Repair Required"
        if r.ruff_issues or r.security_issues:
            return "Passed with Warnings"
        return "Passed"

    # -- main loop -------------------------------------------------------------
    def run(self, text: str, language: str = "Python", constraints: str = "") -> GenerationResult:
        t0 = time.time()
        try:
            spec = requirement_processor.process(text, language, constraints)
        except requirement_processor.RequirementError as e:
            from models import RequirementSpec
            return GenerationResult(spec=RequirementSpec(requirement=text or ""), error=str(e),
                                    trace=[f"Validate input: rejected - {e}"])
        res = GenerationResult(spec=spec)
        res.trace.append(f"Preprocess: action='{spec.action}', entity='{spec.entity}', constraints={spec.constraints}")

        if self.use_tensorflow:
            spec.category, spec.category_confidence = intent_classifier.predict(spec.requirement)
            res.trace.append(f"Understand (TensorFlow classifier): {spec.category} ({spec.category_confidence:.0%})")

        feedback = prev_code = None
        for attempt in range(self.max_repairs + 1):
            try:
                snippet = self.generator.generate(spec, feedback, prev_code)
            except Exception as e:  # network/quota/JSON errors
                res.error = f"Generation failed: {e}"
                res.trace.append(f"Generate (attempt {attempt + 1}): ERROR {e}")
                break
            res.trace.append(f"Generate (attempt {attempt + 1}): Gemini returned '{snippet.function_name}'")
            report = self.review(snippet)
            res.snippet, res.validation = snippet, report
            res.trace.append(
                f"Review: syntax={report.syntax_ok}, security_issues={len(report.security_issues)}, "
                f"ruff={len(report.ruff_issues)}, tests={report.tests_passed}/{report.tests_total}")
            if not report.needs_repair or attempt == self.max_repairs:
                break
            feedback, prev_code = report.feedback(), snippet.code
            res.repair_attempts += 1
            res.trace.append("Repair: sending validation feedback back to the model")

        if res.snippet:
            res.validation.state = self._final_state(res.validation)
            res.spec.assumptions += [a for a in res.snippet.assumptions if a not in res.spec.assumptions]
        res.trace.append(f"Return: state = {res.validation.state}")
        res.latency_sec = round(time.time() - t0, 2)
        return res
