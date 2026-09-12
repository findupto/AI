import json
from pathlib import Path

from evaluation.benchmark import evaluate_cases


def test_sample_benchmark_cases_are_valid():
    path = Path(__file__).parents[1] / "evaluation" / "data" / "smoke_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    report = evaluate_cases(cases)
    assert report["count"] == 2
    assert report["passed"] == 1
