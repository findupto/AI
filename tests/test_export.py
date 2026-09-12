from orchestrator.export import session_to_html, session_to_markdown


MESSAGES = [
    {"role": "user", "content": "Hello <world>", "created_at": "2026-09-12 10:00"},
    {"role": "assistant", "content": "**Welcome**\n\nUse `local AI`.", "created_at": "2026-09-12 10:01"},
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
