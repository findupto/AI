from knowledge.retrieval import LocalRetriever
from orchestrator.loop import AgentLoop
from orchestrator.planner import Planner


def test_planner_creates_bounded_project_plan():
    plan = Planner().create("build a desktop app")
    assert len(plan) == 5
    assert plan[0].title == "Understand"


def test_agent_loop_stops_on_failure():
    plan = Planner().create("test")
    result = AgentLoop(max_steps=5).run(plan, lambda step: step.id != 3)
    assert result.completed == 3
    assert result.completed is not None
    assert plan[2].status == "failed"


def test_local_retriever_ranks_relevant_text():
    rows = [{"text": "Python local project tooling"}, {"text": "apples and oranges"}]
    assert LocalRetriever().rank("Python project", rows, 1)[0]["text"].startswith("Python")
