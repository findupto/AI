import sqlite3
import threading
from pathlib import Path


class MemoryStore:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.RLock()
        with self._lock:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, role TEXT NOT NULL, content TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
            self.db.commit()

    def add(self, role: str, content: str):
        with self._lock:
            self.db.execute("INSERT INTO messages(role, content) VALUES (?, ?)", (role, content))
            self.db.commit()

    def recent(self, limit: int = 12) -> list[dict]:
        limit = max(1, int(limit))
        with self._lock:
            rows = self.db.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def clear(self):
        with self._lock:
            self.db.execute("DELETE FROM messages")
            self.db.commit()
