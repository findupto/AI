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


def test_benchmark_cli(tmp_path, monkeypatch, capsys):
    sample = tmp_path / "cases.json"
    sample.write_text(json.dumps([
        {"id": "ok", "response": "safe local answer", "required": ["safe"]},
    ]), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["benchmark", str(sample)])
    main()
    output = json.loads(capsys.readouterr().out)
    assert output["passed"] == 1
