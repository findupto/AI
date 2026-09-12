import json
import time
from pathlib import Path


class AuditLog:
    """Append-only local JSONL audit trail for tool and project actions."""

    def __init__(self, path: str):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: str, **details):
        entry = {"time": time.time(), "event": event, **details}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry
