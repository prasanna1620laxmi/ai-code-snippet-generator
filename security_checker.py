"""AST-based security scan for generated code."""
import ast
import re

HIGH_CALLS = {"eval", "exec", "__import__", "os.system", "os.popen", "pickle.loads",
              "pickle.load", "shutil.rmtree", "os.remove", "os.unlink", "os.rmdir"}
WARN_IMPORTS = {"socket", "ctypes", "subprocess", "pickle", "marshal", "pty"}
SECRET_NAME = re.compile(r"(password|passwd|secret|api_?key|token)", re.I)


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    return ""


def scan(code: str) -> tuple[list[str], bool]:
    """Return (issues, has_high_severity)."""
    issues: list[str] = []
    high = False
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return [], False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name in HIGH_CALLS:
                issues.append(f"[HIGH] line {node.lineno}: call to {name}()")
                high = True
            elif name.startswith("subprocess."):
                shell = any(k.arg == "shell" and getattr(k.value, "value", False) is True
                            for k in node.keywords)
                issues.append(f"[{'HIGH' if shell else 'WARN'}] line {node.lineno}: {name}()"
                              + (" with shell=True" if shell else ""))
                high = high or shell
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for m in mods:
                if m.split(".")[0] in WARN_IMPORTS:
                    issues.append(f"[WARN] line {node.lineno}: suspicious import '{m}'")
        elif isinstance(node, ast.Assign):
            if (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
                    and node.value.value):
                for t in node.targets:
                    if isinstance(t, ast.Name) and SECRET_NAME.search(t.id):
                        issues.append(f"[HIGH] line {node.lineno}: hardcoded secret in '{t.id}'")
                        high = True
    return issues, high
