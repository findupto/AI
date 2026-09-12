import math
import re
from collections import Counter


class LocalRetriever:
    """Dependency-free relevance scorer for local knowledge when embeddings are unavailable."""

    TOKEN = re.compile(r"[A-Za-z0-9_]{2,}")

    def score(self, query: str, text: str) -> float:
        q = Counter(self.TOKEN.findall(query.lower()))
        d = Counter(self.TOKEN.findall(text.lower()))
        if not q or not d:
            return 0.0
        dot = sum(q[k] * d[k] for k in q)
        norm = math.sqrt(sum(v * v for v in q.values()) * sum(v * v for v in d.values()))
        return dot / norm if norm else 0.0

    def rank(self, query: str, rows, limit: int = 5):
        ranked = sorted(rows, key=lambda row: self.score(query, row.get("text", "")), reverse=True)
        return ranked[: max(1, int(limit))]
