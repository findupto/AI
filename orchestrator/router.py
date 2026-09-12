class ModelRouter:
    """Simple local model routing hook for future specialist GGUF models."""

    def __init__(self, models=None):
        self.models = dict(models or {})

    def register(self, task: str, model):
        self.models[task] = model

    def choose(self, task: str, default):
        return self.models.get(task, self.models.get("general", default))
