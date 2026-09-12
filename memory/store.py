import sqlite3
import threading
from pathlib import Path
from uuid import uuid4


class MemoryStore:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.RLock()
        with self._lock:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
            self.db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT NOT NULL, content TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
            columns = {row[1] for row in self.db.execute("PRAGMA table_info(messages)").fetchall()}
            if "session_id" not in columns:
                self.db.execute("ALTER TABLE messages ADD COLUMN session_id TEXT")
            if not self.db.execute("SELECT 1 FROM sessions LIMIT 1").fetchone():
                session_id = str(uuid4())
                self.db.execute("INSERT INTO sessions(id, title) VALUES (?, ?)", (session_id, "General"))
                self.db.execute("UPDATE messages SET session_id = ? WHERE session_id IS NULL", (session_id,))
            else:
                default_id = self.db.execute("SELECT id FROM sessions ORDER BY created_at LIMIT 1").fetchone()[0]
                self.db.execute("UPDATE messages SET session_id = ? WHERE session_id IS NULL", (default_id,))
            self.db.commit()

    def create_session(self, title: str = "New chat") -> str:
        session_id = str(uuid4())
        title = title.strip() or "New chat"
        with self._lock:
            self.db.execute("INSERT INTO sessions(id, title) VALUES (?, ?)", (session_id, title[:120]))
            self.db.commit()
        return session_id

    def list_sessions(self) -> list[dict]:
        with self._lock:
            rows = self.db.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC").fetchall()
        return [{"id": i, "title": t, "created_at": c} for i, t, c in rows]

    def rename_session(self, session_id: str, title: str):
        with self._lock:
            self.db.execute("UPDATE sessions SET title = ? WHERE id = ?", (title.strip()[:120] or "Untitled", session_id))
            self.db.commit()

    def auto_title(self, session_id: str, text: str):
        title = " ".join(text.strip().split())
        if not title:
            return
        with self._lock:
            current = self.db.execute("SELECT title FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if not current or current[0] not in ("New chat", "Untitled"):
                return
            if len(title) > 48:
                title = title[:45].rstrip() + "..."
            self.db.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
            self.db.commit()

    def delete_session(self, session_id: str):
        with self._lock:
            count = self.db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            if count <= 1:
                return False
            self.db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            self.db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            self.db.commit()
            return True

    def add(self, role: str, content: str, session_id: str | None = None):
        with self._lock:
            if session_id is None:
                session_id = self.db.execute("SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1").fetchone()[0]
            self.db.execute("INSERT INTO messages(session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
            self.db.commit()

    def recent(self, limit: int = 12, session_id: str | None = None) -> list[dict]:
        limit = max(1, int(limit))
        with self._lock:
            if session_id is None:
                session_id = self.db.execute("SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1").fetchone()[0]
            rows = self.db.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?", (session_id, limit)).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def clear(self, session_id: str | None = None):
        with self._lock:
            if session_id is None:
                session_id = self.db.execute("SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1").fetchone()[0]
            self.db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            self.db.commit()

    def close(self):
        with self._lock:
            self.db.close()
