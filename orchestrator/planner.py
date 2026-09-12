from dataclasses import dataclass


@dataclass
class PlanStep:
    id: int
    title: str
    action: str
    status: str = "pending"


class Planner:
    """Small deterministic planning layer; the local model supplies the actual reasoning."""

    def create(self, goal: str) -> list[PlanStep]:
        goal = " ".join(goal.split())
        if not goal:
            return []
        return [
            PlanStep(1, "Understand", f"Inspect requirements and existing project state for: {goal}"),
            PlanStep(2, "Plan", "Choose files, tools, tests, and implementation order."),
            PlanStep(3, "Implement", "Make the smallest coherent project changes."),
            PlanStep(4, "Verify", "Run relevant tests/checks and inspect failures."),
            PlanStep(5, "Report", "Summarize changes, verification, and remaining risks."),
        ]
