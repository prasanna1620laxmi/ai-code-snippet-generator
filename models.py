"""Pydantic schemas shared by every layer of the pipeline."""
from typing import Any, Optional

from pydantic import BaseModel, Field

CATEGORIES = ["Functions", "Algorithms", "APIs", "Classes", "CRUD Operations",
              "Data Processing", "Automation"]


class RequirementSpec(BaseModel):
    requirement: str
    language: str = "Python"
    action: str = ""
    entity: str = ""
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    category: str = "Functions"
    category_confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TestCase(BaseModel):
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    expected: Any = None


class GeneratedSnippet(BaseModel):
    function_name: str
    imports: list[str] = Field(default_factory=list)
    code: str
    explanation: str = ""
    complexity: str = ""
    assumptions: list[str] = Field(default_factory=list)
    test_cases: list[TestCase] = Field(default_factory=list)


class ValidationReport(BaseModel):
    syntax_ok: bool = False
    syntax_error: Optional[str] = None
    structure_ok: bool = False
    security_issues: list[str] = Field(default_factory=list)
    high_severity: bool = False
    ruff_issues: list[str] = Field(default_factory=list)
    cyclomatic: Optional[float] = None
    maintainability: Optional[float] = None
    tests_total: int = 0
    tests_passed: int = 0
    test_failures: list[str] = Field(default_factory=list)
    state: str = "Repair Required"  # Passed | Passed with Warnings | Repair Required | Rejected

    @property
    def needs_repair(self) -> bool:
        return (not self.syntax_ok or not self.structure_ok or self.high_severity
                or self.tests_passed < self.tests_total)

    def feedback(self) -> str:
        parts = []
        if self.syntax_error:
            parts.append(f"Syntax error: {self.syntax_error}")
        if not self.structure_ok:
            parts.append("Code must contain a function/class with a return statement.")
        parts += [f"Security: {i}" for i in self.security_issues]
        parts += [f"Failed test: {f}" for f in self.test_failures]
        return "\n".join(parts)


class GenerationResult(BaseModel):
    spec: RequirementSpec
    snippet: Optional[GeneratedSnippet] = None
    validation: ValidationReport = Field(default_factory=ValidationReport)
    repair_attempts: int = 0
    trace: list[str] = Field(default_factory=list)
    latency_sec: float = 0.0
    error: Optional[str] = None
