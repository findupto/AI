import json

from evaluation.report import main


def test_quality_report_cli(tmp_path, monkeypatch, capsys):
    sample = tmp_path / "responses.txt"
    sample.write_text("hello\n\nlong enough\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["quality-report", str(sample), "--min-length", "2"])
    main()
    report = json.loads(capsys.readouterr().out)
    assert report["count"] == 3
    assert report["passed"] == 2
