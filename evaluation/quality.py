"""Lightweight, dependency-free response quality checks for local evaluation."""

from __future__ import annotations

from collections.abc import Iterable


def score_response(text: str, *, min_length: int = 1) -> dict[str, object]:
    """Return simple deterministic quality signals for an assistant response."""
    value = str(text or "").strip()
    length = len(value)
    return {
        "non_empty": bool(value),
        "minimum_length": length >= max(0, min_length),
        "characters": length,
        "words": len(value.split()),
    }


def evaluate_responses(responses: Iterable[str], *, min_length: int = 1) -> dict[str, object]:
    """Aggregate response quality signals across a collection."""
    items = [score_response(response, min_length=min_length) for response in responses]
    count = len(items)
    passed = sum(bool(item["non_empty"] and item["minimum_length"]) for item in items)
    return {
        "count": count,
        "passed": passed,
        "pass_rate": passed / count if count else 0.0,
        "results": items,
    }
