from pathlib import Path


class LocalLLM:
    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.error = None
        path = Path(config["model"]["path"])
        if not path.exists():
            self.error = f"Local model not found: {path}"
            return
        try:
            from llama_cpp import Llama
            self.model = Llama(
                model_path=str(path),
                n_ctx=config["model"].get("context_size", 8192),
                n_gpu_layers=config["model"].get("gpu_layers", -1),
                n_threads=config["model"].get("threads", 8),
                verbose=False,
            )
        except Exception as exc:
            self.error = f"Could not load local model: {exc}"

    @property
    def ready(self):
        return self.model is not None

    def chat(self, messages: list[dict]) -> str:
        if not self.ready:
            return self.error or "No local model is available."
        result = self.model.create_chat_completion(
            messages=messages,
            temperature=self.config["model"].get("temperature", 0.7),
            max_tokens=self.config["model"].get("max_tokens", 1024),
        )
        return result["choices"][0]["message"]["content"]
