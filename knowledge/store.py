import re
import sqlite3
import threading
from pathlib import Path


class KnowledgeStore:
    def __init__(self, path: str, chunk_size: int = 1200, overlap: int = 150):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.RLock()
        self.chunk_size = max(100, int(chunk_size))
        self.overlap = max(0, min(int(overlap), self.chunk_size - 1))
        with self._lock:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, source TEXT UNIQUE, content TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
            self.db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(source, text)")
            self.db.commit()

    def ingest(self, source: str, text: str):
        with self._lock:
            self.db.execute("INSERT OR REPLACE INTO documents(source, content) VALUES (?, ?)", (source, text))
            self.db.execute("DELETE FROM chunks WHERE source = ?", (source,))
            words = re.findall(r"\S+", text)
            step = max(1, self.chunk_size - self.overlap)
            chunks = [" ".join(words[i:i + self.chunk_size]) for i in range(0, len(words), step)]
            self.db.executemany("INSERT INTO chunks(source, text) VALUES (?, ?)", [(source, c) for c in chunks if c])
            self.db.commit()

    @staticmethod
    def _fts_query(query: str) -> str:
        terms = re.findall(r"[\w]+", query, flags=re.UNICODE)
        return " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms[:16])

    def search(self, query: str, limit: int = 5) -> list[dict]:
        limit = max(1, int(limit))
        fts_query = self._fts_query(query)
        if not fts_query:
            return []
        with self._lock:
            try:
                rows = self.db.execute(
                    "SELECT source, text FROM chunks WHERE chunks MATCH ? ORDER BY rank LIMIT ?",
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = []
        return [{"source": s, "text": t} for s, t in rows]

    def close(self):
        with self._lock:
            self.db.close()
