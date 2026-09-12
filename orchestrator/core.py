import json
from pathlib import Path

from knowledge.ingest import read_document
from knowledge.store import KnowledgeStore
from memory.store import MemoryStore
from models.local_llm import LocalLLM
from security.policy import Policy
from tools.python_tool import run_python

SYSTEM = """You are Findupto AI, a local-first standalone assistant. Be accurate and explicit about uncertainty. Use supplied knowledge context when relevant. Do not claim to have performed an action unless a tool actually performed it. High-impact actions require confirmation. Keep core intelligence local and treat network access as optional."""


class Orchestrator:
    def __init__(self, config_path="config/default.json"):
        config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        self.config = config
        self.policy = Policy(config)
        self.llm = LocalLLM(config)
        self.memory = MemoryStore(config["memory"]["database"])
        self.knowledge = KnowledgeStore(config["knowledge"]["database"], config["knowledge"]["chunk_size"], config["knowledge"]["chunk_overlap"])

    def ingest(self, path: str):
        text = read_document(path)
        self.knowledge.ingest(str(Path(path).resolve()), text)
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
