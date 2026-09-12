import argparse
from pathlib import Path

from orchestrator.core import Orchestrator
from orchestrator.export import session_to_html, session_to_markdown


def select_session(sessions, selector):
    if not selector:
        return None
    selector = selector.strip()
    for session in sessions:
        if session["id"] == selector or session["title"].casefold() == selector.casefold():
            return session
    return None


def main():
    parser = argparse.ArgumentParser(description="Export a Findupto AI conversation.")
    parser.add_argument("output", nargs="?", help="Output .md or .html file")
    parser.add_argument("--session", help="Session ID or exact session title to export")
    parser.add_argument("--list-sessions", action="store_true", help="List saved sessions and exit")
    args = parser.parse_args()

    orchestrator = Orchestrator()
    try:
        sessions = orchestrator.list_sessions()
        if args.list_sessions:
            for session in sessions:
                print(f"{session['id']}\t{session['title']}")
            return
        if not args.output:
            parser.error("output is required unless --list-sessions is used")

        output = Path(args.output).expanduser()
        suffix = output.suffix.lower()
        if suffix not in {".md", ".html"}:
            parser.error("output must end with .md or .html")

        selected = select_session(sessions, args.session)
        if args.session and selected is None:
            parser.error("session not found; use --list-sessions to see available sessions")
        if selected:
            orchestrator.switch_session(selected["id"])
        current = selected or next((s for s in sessions if s["id"] == orchestrator.session_id), None)
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
