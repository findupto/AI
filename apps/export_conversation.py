import argparse
from pathlib import Path

from orchestrator.core import Orchestrator
from orchestrator.export import session_to_html, session_to_markdown


def main():
    parser = argparse.ArgumentParser(description="Export the current Findupto AI conversation.")
    parser.add_argument("output", help="Output .md or .html file")
    args = parser.parse_args()

    output = Path(args.output).expanduser()
    suffix = output.suffix.lower()
    if suffix not in {".md", ".html"}:
        parser.error("output must end with .md or .html")

    orchestrator = Orchestrator()
    try:
        sessions = orchestrator.list_sessions()
        current = next((s for s in sessions if s["id"] == orchestrator.session_id), None)
        title = current["title"] if current else "Conversation"
        messages = orchestrator.session_messages()
        content = session_to_html(messages, title) if suffix == ".html" else session_to_markdown(messages, title)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(output)
    finally:
        orchestrator.memory.close()
        orchestrator.knowledge.close()


if __name__ == "__main__":
    main()
