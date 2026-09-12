"""CLI for running deterministic response-quality checks on text files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.quality import evaluate_responses


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate local AI response samples.")
    parser.add_argument("input", type=Path, help="UTF-8 text file with one response per line")
    parser.add_argument("--min-length", type=int, default=1)
    args = parser.parse_args()

    responses = args.input.read_text(encoding="utf-8").splitlines()
    report = evaluate_responses(responses, min_length=max(0, args.min_length))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
