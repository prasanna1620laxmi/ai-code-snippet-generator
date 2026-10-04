"""Run the agent over data/eval_set.json and print the metrics from the problem statement."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv  # noqa: E402

load_dotenv()
import tester  # noqa: E402
from agent import CodeAgent  # noqa: E402
from code_generator import CodeGenerator  # noqa: E402

cases = json.loads((Path(__file__).parent.parent / "data" / "eval_set.json").read_text())
agent = CodeAgent(CodeGenerator())
n = len(cases)
syntax = struct = func = align = 0
lat = []
for c in cases:
    r = agent.run(c["requirement"])
    lat.append(r.latency_sec)
    if not r.snippet:
        print("FAILED:", c["requirement"], r.error)
        continue
    syntax += r.validation.syntax_ok
    struct += r.validation.structure_ok
    # independent reference tests (not the model's own tests)
    fn = c["function_name"]
    name = fn if f"def {fn}" in r.snippet.code else r.snippet.function_name
    total, passed, _ = tester.run_tests(r.snippet.code, name, c["tests"])
    func += passed == total
    align += c["function_name"].split("_")[-1] in r.snippet.code.lower()
    print(f"{c['function_name']:<24} state={r.validation.state:<22} ref_tests={passed}/{total} {r.latency_sec}s")
print(f"\nFunctional correctness : {func / n:.0%} (target >= 80%)")
print(f"Syntax accuracy        : {syntax / n:.0%} (target >= 95%)")
print(f"Structural completeness: {struct / n:.0%} (target >= 95%)")
print(f"Requirement alignment  : {align / n:.0%} (heuristic, target >= 85%)")
print(f"Avg response time      : {sum(lat) / n:.1f}s (target < 15s)")
