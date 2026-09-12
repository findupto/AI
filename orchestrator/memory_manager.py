from collections import Counter


class ContextManager:
    """Keeps prompts bounded while preserving the newest conversation turns."""

    def __init__(self, max_chars: int = 60_000):
        self.max_chars = max(1000, int(max_chars))

    def trim_messages(self, messages):
        total = 0
        kept = []
        for message in reversed(messages):
            size = len(message.get("content", ""))
            if kept and total + size > self.max_chars:
                break
            kept.append(message)
            total += size
        return list(reversed(kept))

    @staticmethod
    def keywords(text: str, limit: int = 12):
        words = [w.lower() for w in text.split() if len(w) > 3]
        return [word for word, _ in Counter(words).most_common(limit)]
