"""Run simple deterministic benchmark cases against response text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate_case(case: dict[str, object]) -> dict[str, object]:
    response = str(case.get("response", ""))
    required = [str(item).strip() for item in case.get("required", []) or []]
    lowered = response.casefold()
    missing = [item for item in required if item.casefold() not in lowered]
    return {
        "id": str(case.get("id", "")),
        "passed": not missing,
        "missing": missing,
    }


def evaluate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    results = [evaluate_case(case) for case in cases]
    passed = sum(bool(result["passed"]) for result in results)
    return {
        "count": len(results),
        "passed": passed,
        "pass_rate": passed / len(results) if results else 0.0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate local AI benchmark cases.")
    parser.add_argument("input", type=Path, help="UTF-8 JSON file containing a list of cases")
    args = parser.parse_args()
    cases = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_cases(cases), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
