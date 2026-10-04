"""Syntax + structural validation (AST and compile)."""
import ast


def check_syntax(code: str) -> tuple[bool, str | None]:
    try:
        tree = ast.parse(code)
        compile(tree, "<generated>", "exec")
        return True, None
    except SyntaxError as e:
        return False, f"line {e.lineno}: {e.msg}"
    except (ValueError, TypeError) as e:
        return False, str(e)


def check_structure(code: str, function_name: str = "") -> bool:
    """Needs a def/class; functions need a return (or yield)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    defs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if not defs:
        return False
    if function_name and function_name not in {d.name for d in defs}:
        return False
    funcs = [d for d in defs if not isinstance(d, ast.ClassDef)]
    if funcs and not any(isinstance(n, (ast.Return, ast.Yield)) for f in funcs for n in ast.walk(f)):
        # class-only or script-style snippets (e.g. automation) may legitimately not return
        return any(isinstance(d, ast.ClassDef) for d in defs)
    return True
