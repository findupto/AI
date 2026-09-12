from orchestrator.agent import Agent, Tool


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def chat(self, messages):
        return self.response

    def stream(self, messages, on_token, stop_event=None):
        for token in self.response.split(" "):
            on_token(token + " ")
        return self.response


def test_plain_answer_passes_through():
    agent = Agent(FakeLLM("hello"), policy=None)
    assert agent.run("hi") == "hello"
    assert agent.parse_call("hello") is None


def test_streaming_answer_emits_tokens():
    emitted = []
    agent = Agent(FakeLLM("hello world"), policy=None)
    assert agent.run_stream("hi", "", emitted.append) == "hello world"
    assert "hello " in emitted
    assert "world " in emitted


def test_tool_call_is_parsed_without_execution():
    agent = Agent(FakeLLM("TOOL:python\nINPUT:print(2 + 2)"), policy=None)
    agent.register(Tool("python", "calculate", lambda value: (True, value)))
    draft = agent.run("calculate")
    request = agent.parse_call(draft)
    assert request.tool.name == "python"
    assert request.tool_input == "print(2 + 2)"


def test_unknown_tool_is_rejected():
    agent = Agent(FakeLLM("TOOL:unknown\nINPUT:x"), policy=None)
    assert agent.parse_call(agent.run("do it")) is None


def test_tool_result_is_sent_back_to_model():
    class SequenceLLM:
        def __init__(self):
            self.calls = 0

        def chat(self, messages):
            self.calls += 1
            return "final answer" if self.calls > 1 else "unused"

    llm = SequenceLLM()
    agent = Agent(llm, policy=None)
    tool = Tool("python", "calculate", lambda value: (True, "4"))
    request = __import__("orchestrator.agent", fromlist=["ToolRequest"]).ToolRequest(tool, "2+2")
    assert agent.finalize_tool_result("calculate", request, True, "4") == "final answer"
