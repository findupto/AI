from apps.export_conversation import select_session
from orchestrator.export import session_to_html, session_to_json, session_to_markdown


MESSAGES = [
    {"role": "user", "content": "Hello <world>", "created_at": "2026-09-12 10:00"},
    {"role": "assistant", "content": "**Welcome**\n\nUse `local AI`.", "created_at": "2026-09-12 10:01"},
]

SESSIONS = [
    {"id": "abc", "title": "General", "created_at": "2026-09-12 09:00"},
    {"id": "def", "title": "Project Chat", "created_at": "2026-09-12 09:01"},
]


def test_session_to_markdown_preserves_order_and_content():
    output = session_to_markdown(MESSAGES, "My Chat")
    assert output.startswith("# My Chat\n")
    assert output.index("Hello <world>") < output.index("**Welcome**")
    assert "## You — 2026-09-12 10:00" in output


def test_session_to_html_escapes_content():
    output = session_to_html(MESSAGES, "My Chat")
    assert "<title>My Chat</title>" in output
    assert "Hello &lt;world&gt;" in output
    assert "<b>Welcome</b>" not in output
    assert "**Welcome**" in output


def test_session_to_json_preserves_structure_and_unicode():
    import json

    output = session_to_json(MESSAGES, "My Chat")
    payload = json.loads(output)
    assert payload["title"] == "My Chat"
    assert payload["messages"][0]["content"] == "Hello <world>"
    assert payload["messages"][1]["role"] == "assistant"


def test_select_session_matches_id_or_title_case_insensitively():
    assert select_session(SESSIONS, "def")["title"] == "Project Chat"
    assert select_session(SESSIONS, "project chat")["id"] == "def"
    assert select_session(SESSIONS, "missing") is None
