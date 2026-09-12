import json

from evaluation.benchmark import evaluate_case, evaluate_cases, main


def test_evaluate_case_is_case_insensitive():
    result = evaluate_case({"id": "greeting", "response": "Hello Local AI", "required": ["local ai"]})
    assert result["passed"] is True
    assert result["missing"] == []


def test_evaluate_cases_reports_missing_requirements():
    result = evaluate_cases([
        {"id": "one", "response": "alpha beta", "required": ["alpha"]},
        {"id": "two", "response": "alpha", "required": ["beta"]},
    ])
    assert result["count"] == 2
    assert result["passed"] == 1
    assert result["pass_rate"] == 0.5
    assert result["results"][1]["missing"] == ["beta"]


def test_evaluate_case_supports_forbidden_and_min_length():
    passing = evaluate_case({"id": "safe", "response": "alpha beta", "required": ["alpha"], "forbidden": ["danger"], "min_length": 8})
    failing = evaluate_case({"id": "unsafe", "response": "danger", "forbidden": ["danger"]})
    short = evaluate_case({"id": "short", "response": "ok", "min_length": 3})
    assert passing["passed"] is True
    assert failing["forbidden"] == ["danger"]
    assert failing["passed"] is False
    assert short["passed"] is False


def test_benchmark_cli(tmp_path, monkeypatch, capsys):
    sample = tmp_path / "cases.json"
    sample.write_text(json.dumps([
        {"id": "ok", "response": "safe local answer", "required": ["safe"]},
    ]), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["benchmark", str(sample)])
    main()
    output = json.loads(capsys.readouterr().out)
    assert output["passed"] == 1
