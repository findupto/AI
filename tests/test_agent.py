from orchestrator.agent import Agent, Tool


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def chat(self, messages):
        return self.response


def test_plain_answer_passes_through():
    agent = Agent(FakeLLM("hello"), policy=None)
    assert agent.run("hi") == "hello"
    assert agent.parse_call("hello") is None


def test_tool_call_is_parsed_without_execution():
    agent = Agent(FakeLLM("TOOL:python\nINPUT:print(2 + 2)"), policy=None)
    agent.register(Tool("python", "calculate", lambda value: (True, value)))
    draft = agent.run("calculate")
    tool, value = agent.parse_call(draft)
    assert tool.name == "python"
    assert value == "print(2 + 2)"


def test_unknown_tool_is_rejected():
    agent = Agent(FakeLLM("TOOL:unknown\nINPUT:x"), policy=None)
    assert agent.parse_call(agent.run("do it")) is None
