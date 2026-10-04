"""Ruff (lint) and Radon (complexity). Both degrade gracefully if missing."""
import json
import subprocess
import sys


def ruff_issues(code: str) -> list[str]:
    try:
        p = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--select", "E,F,W,B", "--ignore", "E501",
             "--output-format", "json", "--stdin-filename", "snippet.py", "-"],
            input=code, capture_output=True, text=True, timeout=15)
        data = json.loads(p.stdout or "[]")
        return [f"{d['code']} line {d['location']['row']}: {d['message']}" for d in data]
    except Exception:
        return []


def complexity(code: str) -> tuple[float | None, float | None]:
    try:
        from radon.complexity import cc_visit
        from radon.metrics import mi_visit
        blocks = cc_visit(code)
        cc = max((b.complexity for b in blocks), default=1)
        return float(cc), round(float(mi_visit(code, multi=True)), 1)
    except Exception:
        return None, None
