"""SQLite history of generations."""
import sqlite3
from pathlib import Path

from models import GenerationResult

DB_PATH = Path(__file__).parent / "data" / "history.db"


def _conn(path: Path = DB_PATH) -> sqlite3.Connection:
    c = sqlite3.connect(path)
    c.execute("""CREATE TABLE IF NOT EXISTS generations(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        requirement TEXT, category TEXT, state TEXT, payload TEXT)""")
    return c


def save(result: GenerationResult, path: Path = DB_PATH) -> int:
    with _conn(path) as c:
        cur = c.execute("INSERT INTO generations(requirement, category, state, payload) VALUES (?,?,?,?)",
                        (result.spec.requirement, result.spec.category, result.validation.state,
                         result.model_dump_json()))
        return cur.lastrowid


def list_history(limit: int = 50, path: Path = DB_PATH) -> list[dict]:
    with _conn(path) as c:
        rows = c.execute("SELECT id, created_at, requirement, category, state FROM generations "
                         "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(zip(("id", "created_at", "requirement", "category", "state"), r)) for r in rows]


def get(gen_id: int, path: Path = DB_PATH) -> GenerationResult | None:
    with _conn(path) as c:
        row = c.execute("SELECT payload FROM generations WHERE id=?", (gen_id,)).fetchone()
    return GenerationResult.model_validate_json(row[0]) if row else None
