from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[[str], tuple[bool, str]]
    requires_confirmation: bool = True


class Agent:
    """Small, model-agnostic tool loop for the local orchestrator."""

    def __init__(self, llm, policy):
        self.llm = llm
        self.policy = policy
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def tool_catalog(self) -> str:
        if not self.tools:
            return "No tools are currently available."
        return "\n".join(f"- {t.name}: {t.description}" for t in self.tools.values())

    def run(self, user_text: str, context: str = "") -> str:
        """Ask the local model for an answer; tool execution is explicit and bounded.

        The model is never allowed to silently execute a tool. Tool calls use the
        simple ACTION format: TOOL:<name>\nINPUT:<text>. The UI can confirm them
        before the handler is invoked.
        """
        prompt = (
            "You are the Findupto AI agent. Answer directly when no tool is needed.\n"
            "Available tools:\n" + self.tool_catalog() + "\n\n"
            "If a tool is genuinely required, emit exactly:\n"
            "TOOL:<tool name>\nINPUT:<tool input>\n"
            "Otherwise answer normally.\n"
            + ("Local context:\n" + context + "\n" if context else "")
            + "User request: " + user_text
        )
        return self.llm.chat([
            {"role": "system", "content": "You are a local tool-using assistant."},
            {"role": "user", "content": prompt},
        ])

    def parse_call(self, text: str):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 2 or not lines[0].startswith("TOOL:") or not lines[1].startswith("INPUT:"):
            return None
        name = lines[0][5:].strip()
        if name not in self.tools:
            return None
        return self.tools[name], lines[1][6:].strip()
