"""Run simple deterministic benchmark cases against response text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate_case(case: dict[str, object]) -> dict[str, object]:
    response = str(case.get("response", ""))
    required = [str(item).strip() for item in case.get("required", []) or []]
    forbidden = [str(item).strip() for item in case.get("forbidden", []) or []]
    min_length = max(0, int(case.get("min_length", 0) or 0))
    lowered = response.casefold()
    missing = [item for item in required if item.casefold() not in lowered]
    found_forbidden = [item for item in forbidden if item.casefold() in lowered]
    too_short = len(response.strip()) < min_length
    return {
        "id": str(case.get("id", "")),
        "passed": not missing and not found_forbidden and not too_short,
        "missing": missing,
        "forbidden": found_forbidden,
        "length": len(response.strip()),
        "min_length": min_length,
    }


def evaluate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    results = [evaluate_case(case) for case in cases]
    passed = sum(bool(result["passed"]) for result in results)
    return {
        "count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate": passed / len(results) if results else 0.0,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate local AI benchmark cases.")
    parser.add_argument("input", type=Path, help="UTF-8 JSON file containing a list of cases")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit with status 1 when any case fails")
    args = parser.parse_args()
    cases = json.loads(args.input.read_text(encoding="utf-8"))
    report = evaluate_cases(cases)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on_error and report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
