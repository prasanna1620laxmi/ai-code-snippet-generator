"""Functional testing: run reference cases in an isolated subprocess with a timeout."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

RUNNER = '''
import json, sys, importlib.util
spec = importlib.util.spec_from_file_location("candidate", sys.argv[1])
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
fn = getattr(mod, sys.argv[2])
out = []
for c in json.load(open(sys.argv[3])):
    try:
        r = fn(*c.get("args", []), **c.get("kwargs", {}))
        out.append({"ok": r == c.get("expected"), "got": repr(r)})
    except Exception as e:
        out.append({"ok": False, "got": f"{type(e).__name__}: {e}"})
print("@@RESULT@@" + json.dumps(out))
'''


def run_tests(code: str, function_name: str, cases: list[dict], timeout: int = 8) -> tuple[int, int, list[str]]:
    """Return (total, passed, failure_messages)."""
    if not cases or not function_name:
        return 0, 0, []
    with tempfile.TemporaryDirectory() as d:
        dp = Path(d)
        (dp / "candidate.py").write_text(code)
        (dp / "runner.py").write_text(RUNNER)
        (dp / "cases.json").write_text(json.dumps(cases))
        try:
            p = subprocess.run([sys.executable, "-I", "runner.py", "candidate.py", function_name, "cases.json"],
                               cwd=d, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return len(cases), 0, [f"Timed out after {timeout}s"]
        line = next((l for l in p.stdout.splitlines() if l.startswith("@@RESULT@@")), None)
        if line is None:
            return len(cases), 0, [f"Execution failed: {p.stderr.strip()[-300:]}"]
        results = json.loads(line[len("@@RESULT@@"):])
    fails = [f"{function_name}{tuple(c.get('args', []))} expected {c.get('expected')!r}, got {r['got']}"
             for c, r in zip(cases, results) if not r["ok"]]
    return len(cases), len(cases) - len(fails), fails
