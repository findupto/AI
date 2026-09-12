import json
import sys
from pathlib import Path

from knowledge.ingest import read_document
from knowledge.store import KnowledgeStore
from memory.store import MemoryStore
from models.local_llm import LocalLLM
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
        self.knowledge = KnowledgeStore(
            self._data_path(config["knowledge"]["database"]),
            config["knowledge"]["chunk_size"],
            config["knowledge"]["chunk_overlap"],
        )

    def _data_path(self, value: str) -> str:
        path = Path(value).expanduser()
        return str(path if path.is_absolute() else self.base_dir / path)

    def ingest(self, path: str):
        document = Path(path).expanduser().resolve()
        text = read_document(str(document))
        self.knowledge.ingest(str(document), text)
        return len(text)

    def answer(self, user_text: str) -> str:
        self.memory.add("user", user_text)
        context_rows = self.knowledge.search(user_text, 4)
        context = "\n\n".join(f"SOURCE: {r['source']}\n{r['text']}" for r in context_rows)
        messages = [{"role": "system", "content": SYSTEM}]
        if context:
            messages.append({"role": "system", "content": "Relevant local knowledge:\n" + context})
        messages.extend(self.memory.recent(12))
        response = self.llm.chat(messages)
        self.memory.add("assistant", response)
        return response

    def execute_python(self, code: str):
        if self.policy.tool_confirmation_required():
            return False, "Python tool requires explicit user confirmation in the desktop UI."
        return run_python(code, self.policy.python_timeout())
