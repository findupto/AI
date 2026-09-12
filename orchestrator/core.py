import json
import sys
from pathlib import Path
from threading import Event

from knowledge.ingest import read_document
from knowledge.store import KnowledgeStore
from memory.store import MemoryStore
from models.local_llm import LocalLLM
from orchestrator.agent import Agent, Tool, ToolRequest
from security.policy import Policy
from tools.python_tool import run_python

SYSTEM = """You are Findupto AI, a local-first standalone assistant. Be accurate and explicit about uncertainty. Use supplied knowledge context when relevant. Do not claim to have performed an action unless a tool actually performed it. High-impact actions require confirmation. Keep core intelligence local and treat network access as optional."""


class Orchestrator:
    def __init__(self, config_path=None):
        project_root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
        config_file = Path(config_path).expanduser() if config_path else project_root / "config" / "default.json"
        if not config_file.is_absolute():
            config_file = project_root / config_file
        config_file = config_file.resolve()
        self.base_dir = project_root
        config = json.loads(config_file.read_text(encoding="utf-8"))
        self.config = config
        self.policy = Policy(config)
        self.llm = LocalLLM(config, base_dir=self.base_dir)
        self.memory = MemoryStore(self._data_path(config["memory"]["database"]))
        self.knowledge = KnowledgeStore(self._data_path(config["knowledge"]["database"]), config["knowledge"]["chunk_size"], config["knowledge"]["chunk_overlap"])
        self.agent = Agent(self.llm, self.policy)
        self.session_id = self.memory.list_sessions()[0]["id"]
        self.agent.register(Tool("python", "Run bounded Python for calculations and local text processing", self.execute_python, requires_confirmation=True))

    def _data_path(self, value: str) -> str:
        path = Path(value).expanduser()
        return str(path if path.is_absolute() else self.base_dir / path)

    def ingest(self, path: str):
        document = Path(path).expanduser().resolve()
        text = read_document(str(document))
        self.knowledge.ingest(str(document), text)
        return len(text)

    def list_documents(self):
        return self.knowledge.documents()

    def delete_document(self, source: str):
        return self.knowledge.delete(source)

    def _context(self, user_text: str):
        rows = self.knowledge.search(user_text, 4)
        context = "\n\n".join(f"SOURCE: {r['source']}\n{r['text']}" for r in rows)
        sources = list(dict.fromkeys(r["source"] for r in rows))
        return context, sources

    def list_sessions(self):
        return self.memory.list_sessions()

    def new_session(self, title: str = "New chat"):
        self.session_id = self.memory.create_session(title)
        return self.session_id

    def switch_session(self, session_id: str):
        if any(s["id"] == session_id for s in self.memory.list_sessions()):
            self.session_id = session_id
            return True
        return False

    def rename_session(self, title: str):
        self.memory.rename_session(self.session_id, title)

    def delete_session(self, session_id: str):
        deleted = self.memory.delete_session(session_id)
        if deleted and session_id == self.session_id:
            self.session_id = self.memory.list_sessions()[0]["id"]
        return deleted

    def session_messages(self):
        return self.memory.recent(200, self.session_id)

    def _record_user(self, user_text: str):
        self.memory.auto_title(self.session_id, user_text)
        self.memory.add("user", user_text, self.session_id)

    def answer(self, user_text: str) -> str:
        self._record_user(user_text)
        context, _ = self._context(user_text)
        messages = [{"role": "system", "content": SYSTEM}]
        if context:
            messages.append({"role": "system", "content": "Relevant local knowledge:\n" + context})
        messages.extend(self.memory.recent(12, self.session_id))
        response = self.llm.chat(messages)
        self.memory.add("assistant", response, self.session_id)
        return response

    def execute_python(self, code: str):
        if self.policy.tool_confirmation_required():
            return False, "Python tool requires explicit user confirmation in the desktop UI."
        return run_python(code, self.policy.python_timeout())

    def prepare_agent_request(self, user_text: str):
        self._record_user(user_text)
        context, sources = self._context(user_text)
        draft = self.agent.run(user_text, context)
        request = self.agent.parse_call(draft)
        if request is None:
            self.memory.add("assistant", draft, self.session_id)
            return {"kind": "answer", "text": draft, "sources": sources}
        if not request.tool.requires_confirmation:
            ok, result = request.tool.handler(request.tool_input)
            final = self.agent.finalize_tool_result(user_text, request, ok, result)
            self.memory.add("assistant", final, self.session_id)
            return {"kind": "answer", "text": final, "sources": sources}
        return {"kind": "tool_request", "text": draft, "user_text": user_text, "tool": request.tool.name, "input": request.tool_input, "sources": sources}

    def prepare_agent_request_stream(self, user_text: str, on_token, stop_event: Event | None = None):
        self._record_user(user_text)
        context, sources = self._context(user_text)
        draft = self.agent.run_stream(user_text, context, on_token, stop_event)
        if stop_event and stop_event.is_set():
            if draft:
                self.memory.add("assistant", draft, self.session_id)
            return {"kind": "stopped", "text": draft, "sources": sources}
        request = self.agent.parse_call(draft)
        if request is None:
            self.memory.add("assistant", draft, self.session_id)
            return {"kind": "answer", "text": draft, "sources": sources}
        return {"kind": "tool_request", "text": draft, "user_text": user_text, "tool": request.tool.name, "input": request.tool_input, "sources": sources}

    def approve_tool(self, user_text: str, tool_name: str, tool_input: str):
        tool = self.agent.tools.get(tool_name)
        if tool is None:
            return "Tool is no longer available."
        if not tool.requires_confirmation:
            return "This tool did not require approval."
        ok, result = tool.handler(tool_input)
        final = self.agent.finalize_tool_result(user_text, ToolRequest(tool, tool_input), ok, result)
        self.memory.add("assistant", final, self.session_id)
        return final

    def reject_tool(self, user_text: str, tool_name: str, tool_input: str):
        message = f"I did not run the '{tool_name}' tool. The requested action was rejected."
        self.memory.add("assistant", message, self.session_id)
        return message

    def agent_answer(self, user_text: str) -> str:
        result = self.prepare_agent_request(user_text)
        if result["kind"] == "answer":
            return result["text"]
        return f"Tool confirmation required: {result['tool']}\nINPUT: {result['input']}\n\nApprove this tool request in the desktop UI."
