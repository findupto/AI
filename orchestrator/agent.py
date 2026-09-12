from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[[str], tuple[bool, str]]
    requires_confirmation: bool = True


@dataclass
class ToolRequest:
    tool: Tool
    tool_input: str


class Agent:
    """Model-agnostic agent loop with explicit tool approval."""

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
        return ToolRequest(self.tools[name], lines[1][6:].strip())

    def finalize_tool_result(self, user_text: str, request: ToolRequest, ok: bool, result: str) -> str:
        status = "succeeded" if ok else "failed"
        prompt = (
            f"The approved tool '{request.tool.name}' {status}.\n"
            f"Tool input: {request.tool_input}\n"
            f"Tool result:\n{result}\n\n"
            f"Original user request: {user_text}\n"
            "Give the user a concise final answer. Do not claim anything beyond the tool result."
        )
        return self.llm.chat([
            {"role": "system", "content": "You are Findupto AI, a local-first assistant."},
            {"role": "user", "content": prompt},
        ])
