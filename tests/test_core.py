import pytest

import requirement_processor as rp
import security_checker
import tester
import validator
from agent import CodeAgent
from models import GeneratedSnippet

GOOD = "def is_prime(n: int) -> bool:\n    if n <= 1:\n        return False\n    return all(n % d for d in range(2, int(n ** 0.5) + 1))\n"


def test_requirement_extraction():
    s = rp.process("Create a function to calculate factorial using recursion.")
    assert s.action in ("create", "calculate")
    assert "Use recursion" in s.constraints


@pytest.mark.parametrize("bad", ["", "   ", "hi"])
def test_bad_requirements(bad):
    with pytest.raises(rp.RequirementError):
        rp.process(bad)


def test_syntax_and_structure():
    assert validator.check_syntax(GOOD)[0]
    assert not validator.check_syntax("def f(:\n  pass")[0]
    assert validator.check_structure(GOOD, "is_prime")
    assert not validator.check_structure("x = 1")


def test_security():
    issues, high = security_checker.scan("import os\ndef f(c):\n    os.system(c)\n")
    assert high and issues
    assert security_checker.scan("password = 'abc123'\n")[1]
    assert not security_checker.scan(GOOD)[1]


def test_tester():
    total, passed, fails = tester.run_tests(GOOD, "is_prime", [{"args": [7], "expected": True}, {"args": [8], "expected": True}])
    assert (total, passed) == (2, 1) and fails
    assert tester.run_tests("def f():\n    while True: pass\n", "f", [{"args": [], "expected": 1}], timeout=2)[1] == 0


class FakeGen:
    """First attempt is wrong, second is right -> exercises the repair loop."""
    def __init__(self):
        self.calls = 0

    def generate(self, spec, feedback=None, previous_code=None):
        self.calls += 1
        code = GOOD if feedback else GOOD.replace("n <= 1", "n < 0")
        return GeneratedSnippet(function_name="is_prime", code=code, complexity="O(sqrt(n))",
                                test_cases=[{"args": [1], "expected": False}, {"args": [7], "expected": True}])


def test_agent_repairs():
    gen = FakeGen()
    res = CodeAgent(gen, max_repairs=2, use_tensorflow=False).run("Create a function to check whether a number is prime.")
    assert gen.calls == 2 and res.repair_attempts == 1
    assert res.validation.state in ("Passed", "Passed with Warnings")
