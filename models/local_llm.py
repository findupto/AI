import os
from pathlib import Path
from threading import Event


class LocalLLM:
    def __init__(self, config: dict, base_dir: Path | None = None):
        self.config = config
        self.model = None
        self.error = None
        self.base_dir = (base_dir or Path.cwd()).resolve()
        raw_path = os.getenv("FINDUPTO_MODEL_PATH", config["model"]["path"])
        self.load_model(raw_path)

    def resolve_path(self, raw_path: str | os.PathLike) -> Path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = self.base_dir / path
        return path.resolve()

    def load_model(self, raw_path: str | os.PathLike) -> bool:
        path = self.resolve_path(raw_path)
        self.model = None
        self.error = None
        if not path.exists():
            self.error = f"Local model not found: {path}"
            return False
        if not path.is_file():
            self.error = f"Local model path is not a file: {path}"
            return False
        if path.suffix.lower() != ".gguf":
            self.error = f"Unsupported local model format: {path.suffix or 'unknown'} (expected .gguf)"
            return False
        try:
            from llama_cpp import Llama
            self.model = Llama(
                model_path=str(path),
                n_ctx=self.config["model"].get("context_size", 8192),
                n_gpu_layers=self.config["model"].get("gpu_layers", -1),
                n_threads=self.config["model"].get("threads", 8),
                verbose=False,
            )
            self.config["model"]["path"] = str(path)
            return True
        except Exception as exc:
            self.error = f"Could not load local model: {exc}"
            return False

    @property
    def ready(self):
        return self.model is not None

    @property
    def model_path(self):
        return self.config["model"].get("path", "")

    def chat(self, messages: list[dict]) -> str:
        if not self.ready:
            return self.error or "No local model is available."
        result = self.model.create_chat_completion(
            messages=messages,
            temperature=self.config["model"].get("temperature", 0.7),
            max_tokens=self.config["model"].get("max_tokens", 1024),
        )
        return result["choices"][0]["message"]["content"]

    def stream(self, messages: list[dict], on_token, stop_event: Event | None = None) -> str:
        if not self.ready:
            text = self.error or "No local model is available."
            on_token(text)
            return text
        parts = []
        for chunk in self.model.create_chat_completion(
            messages=messages,
            temperature=self.config["model"].get("temperature", 0.7),
            max_tokens=self.config["model"].get("max_tokens", 1024),
            stream=True,
        ):
            if stop_event and stop_event.is_set():
                break
            token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if token:
                parts.append(token)
                on_token(token)
        return "".join(parts)
