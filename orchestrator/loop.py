from dataclasses import dataclass


@dataclass
class LoopResult:
    completed: bool
    steps: int
    message: str


class AgentLoop:
    """Bounded orchestration loop; execution remains tool/policy controlled."""

    def __init__(self, max_steps: int = 8):
        self.max_steps = max(1, int(max_steps))

    def run(self, steps, execute):
        completed = 0
        for step in steps[: self.max_steps]:
            ok = bool(execute(step))
            step.status = "done" if ok else "failed"
            completed += 1
            if not ok:
                return LoopResult(False, completed, f"Stopped at step {step.id}: {step.title}")
        return LoopResult(True, completed, "Plan completed within the configured step limit.")
