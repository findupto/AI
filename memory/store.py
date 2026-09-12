import sqlite3
from pathlib import Path


class MemoryStore:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, role TEXT, content TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
        self.db.commit()

    def add(self, role: str, content: str):
        self.db.execute("INSERT INTO messages(role, content) VALUES (?, ?)", (role, content))
        self.db.commit()

    def recent(self, limit: int = 12) -> list[dict]:
        rows = self.db.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]
