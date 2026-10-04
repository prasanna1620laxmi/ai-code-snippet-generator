"""Stage 1-2: validate, normalise and extract structure from a requirement."""
import re

from models import RequirementSpec

ACTIONS = ["create", "build", "write", "implement", "calculate", "compute", "check",
           "validate", "sort", "filter", "parse", "convert", "generate", "read", "find",
           "fetch", "delete", "update", "process", "merge", "count", "reverse", "send",
           "rename", "extract", "clean"]
SKIP = {"a", "an", "the", "python", "function", "class", "script", "program", "that",
        "to", "which", "for", "whether", "if", "code", "snippet", "method", "api"}
STOP = {"using", "with", "and", "from", "in", "on", "by", "that", "which", "returns",
        "return", "given", "takes", "accepts", "to", "of", "for", "is", "are"}
CONSTRAINTS = {
    "Use recursion": r"\brecurs",
    "Use iteration": r"\biterat|\bloop",
    "Include type hints": r"type hint",
    "No external libraries": r"(without|no) (any )?(external |third[- ]party )?librar",
    "Include error handling": r"error handling|handle (errors|exceptions)",
    "Include docstring": r"docstring",
}


class RequirementError(ValueError):
    pass


def normalize(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text or "", flags=re.S)
    text = re.sub(r"^[\s\-*\u2022\d.)]+", "", text.strip())
    return re.sub(r"\s+", " ", text).strip()


def _extract_entity(words: list[str], action: str) -> str:
    if action not in words:
        return ""
    ent = []
    for w in words[words.index(action) + 1:]:
        lw = w.lower().strip(".,")
        if lw in SKIP and not ent:
            continue
        if lw in STOP and ent:
            break
        if lw in SKIP:
            continue
        ent.append(lw)
        if len(ent) == 3:
            break
    return " ".join(ent)


def process(text: str, language: str = "Python", extra_constraints: str = "") -> RequirementSpec:
    clean = normalize(text)
    if not clean:
        raise RequirementError("Requirement is empty.")
    if len(clean.split()) < 3:
        raise RequirementError("Requirement is too short/ambiguous; add more detail.")

    spec = RequirementSpec(requirement=clean, language=language)
    words = clean.split()
    low = [w.lower().strip(".,") for w in words]
    spec.action = next((a for a in ACTIONS if a in low), "")
    spec.entity = _extract_entity(low, spec.action)

    for label, pat in CONSTRAINTS.items():
        if re.search(pat, clean, re.I):
            spec.constraints.append(label)
    if extra_constraints.strip():
        spec.constraints += [c.strip() for c in re.split(r"[;\n]", extra_constraints) if c.strip()]

    m_in = re.search(r"(?:takes|accepts|given|input[s]?)\s+(?:an?\s+|the\s+)?([\w ,]+?)(?:\s+and|\.|,|$)", clean, re.I)
    m_out = re.search(r"returns?\s+(.+?)(?:\.|$)", clean, re.I)
    if m_in:
        spec.inputs.append(m_in.group(1).strip())
    if m_out:
        spec.outputs.append(m_out.group(1).strip())
    if not spec.inputs:
        spec.assumptions.append("Input types were not stated; the model will infer them.")
    if not spec.outputs:
        spec.assumptions.append("Return value was not stated; the model will infer it.")
    if len(words) < 6:
        spec.warnings.append("Short requirement - result may rely on assumptions.")
    if not spec.action:
        spec.warnings.append("No clear action verb detected.")
    return spec
