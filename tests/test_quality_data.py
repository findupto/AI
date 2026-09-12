import json
from pathlib import Path

from evaluation.benchmark import evaluate_cases


def test_quality_benchmark_examples_pass():
    path = Path(__file__).parents[1] / "evaluation" / "data" / "quality_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    report = evaluate_cases(cases)
    assert report["count"] == 2
    assert report["passed"] == 2
    assert report["pass_rate"] == 1.0
