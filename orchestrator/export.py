from html import escape


def session_to_markdown(messages, title="Conversation"):
    """Render persisted session messages as portable Markdown."""
    lines = [f"# {title.strip() or 'Conversation'}", ""]
    for message in messages:
        role = "You" if message.get("role") == "user" else "Findupto AI"
        timestamp = message.get("created_at")
        heading = f"## {role}"
        if timestamp:
            heading += f" — {timestamp}"
        lines.extend([heading, "", str(message.get("content", "")), ""])
    return "\n".join(lines).rstrip() + "\n"


def session_to_html(messages, title="Conversation"):
    """Render persisted session messages as a self-contained HTML document."""
    title = title.strip() or "Conversation"
    blocks = [
        "<!doctype html>",
        '<html><head><meta charset="utf-8">',
        f"<title>{escape(title)}</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 20px;line-height:1.6}"
        ".message{margin:18px 0;padding:14px 18px;border:1px solid #ddd;border-radius:10px}"
        ".meta{font-size:.85em;color:#666;margin-bottom:8px}pre{white-space:pre-wrap}</style></head>",
        f"<body><h1>{escape(title)}</h1>",
    ]
    for message in messages:
        role = "You" if message.get("role") == "user" else "Findupto AI"
        timestamp = message.get("created_at")
        meta = role + (f" — {timestamp}" if timestamp else "")
        content = escape(str(message.get("content", "")))
        blocks.append(f'<section class="message"><div class="meta">{escape(meta)}</div><pre>{content}</pre></section>')
    blocks.append("</body></html>")
    return "\n".join(blocks)
