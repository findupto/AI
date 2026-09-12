import json
from pathlib import Path


def test_default_config_is_valid():
    config = json.loads(Path("config/default.json").read_text(encoding="utf-8"))
    assert config["app_name"] == "Findupto AI"
    assert config["security"]["allow_network"] is False


def test_python_tool_timeout_and_bounded_builtins():
    from tools.python_tool import run_python

    ok, output = run_python("print(sum([1, 2, 3]))", timeout=2)
    assert ok is True
    assert output.strip() == "6"

    ok, _ = run_python("import os", timeout=2)
    assert ok is False

    ok, message = run_python("while True: pass", timeout=1)
    assert ok is False
    assert "timed out" in message.lower()
