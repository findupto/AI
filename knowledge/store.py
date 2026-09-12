import re, sqlite3
from pathlib import Path


class KnowledgeStore:
    def __init__(self, path: str, chunk_size: int = 1200, overlap: int = 150):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.chunk_size, self.overlap = chunk_size, overlap
        self.db.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, source TEXT UNIQUE, content TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
        self.db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(source, text)")
        self.db.commit()

    def ingest(self, source: str, text: str):
        self.db.execute("INSERT OR REPLACE INTO documents(source, content) VALUES (?, ?)", (source, text))
        self.db.execute("DELETE FROM chunks WHERE source = ?", (source,))
        words = re.findall(r"\S+", text)
        step = max(1, self.chunk_size - self.overlap)
        chunks = [" ".join(words[i:i+self.chunk_size]) for i in range(0, len(words), step)]
        self.db.executemany("INSERT INTO chunks(source, text) VALUES (?, ?)", [(source, c) for c in chunks if c])
        self.db.commit()

    def search(self, query: str, limit: int = 5) -> list[dict]:
        try:
            rows = self.db.execute("SELECT source, text FROM chunks WHERE chunks MATCH ? LIMIT ?", (query, limit)).fetchall()
        except sqlite3.OperationalError:
            rows = []
        return [{"source": s, "text": t} for s, t in rows]
