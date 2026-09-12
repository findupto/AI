import os
from pathlib import Path


class LocalDrive:
    """Bounded local workspace for AI project work.

    Paths are resolved beneath the configured root; traversal outside the root is rejected.
    This is a workspace boundary, not a security sandbox.
    """

    def __init__(self, root: str, max_file_bytes: int = 2_000_000, max_read_bytes: int = 1_000_000):
        self.root = Path(root).expanduser().resolve()
        self.max_file_bytes = max(1, int(max_file_bytes))
        self.max_read_bytes = max(1, int(max_read_bytes))
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Path is outside LocalDrive workspace") from exc
        return candidate

    def list_directory(self, relative: str = ".") -> list[dict]:
        directory = self.path(relative)
        if not directory.is_dir():
            raise ValueError("Not a directory")
        return [
            {"name": p.name, "type": "directory" if p.is_dir() else "file", "size": p.stat().st_size if p.is_file() else 0}
            for p in sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        ]

    def read_file(self, relative: str) -> str:
        file_path = self.path(relative)
        if not file_path.is_file():
            raise ValueError("Not a file")
        if file_path.stat().st_size > self.max_read_bytes:
            raise ValueError("File exceeds configured read limit")
        return file_path.read_text(encoding="utf-8", errors="replace")

    def write_file(self, relative: str, text: str) -> str:
        file_path = self.path(relative)
        data = text.encode("utf-8")
        if len(data) > self.max_file_bytes:
            raise ValueError("File exceeds configured write limit")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return str(file_path.relative_to(self.root))

    def search(self, query: str, relative: str = ".", limit: int = 100) -> list[str]:
        query = query.strip().lower()
        if not query:
            return []
        base = self.path(relative)
        if not base.is_dir():
            raise ValueError("Not a directory")
        results = []
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".venv", "venv", "node_modules"}]
            for name in files:
                path = Path(root) / name
                if len(results) >= limit:
                    return results
                try:
                    if query in name.lower():
                        results.append(str(path.relative_to(self.root)))
                        continue
                    if path.stat().st_size <= self.max_read_bytes and query in path.read_text(encoding="utf-8", errors="ignore").lower():
                        results.append(str(path.relative_to(self.root)))
                except OSError:
                    continue
        return results

    def inspect_project(self, relative: str = ".") -> dict:
        root = self.path(relative)
        if not root.is_dir():
            raise ValueError("Not a directory")
        markers = {
            "python": ["pyproject.toml", "requirements.txt", "setup.py"],
            "javascript": ["package.json", "tsconfig.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod"],
        }
        found = []
        for language, names in markers.items():
            if any((root / name).exists() for name in names):
                found.append(language)
        return {
            "root": str(root),
            "languages": found,
            "git": (root / ".git").exists(),
            "files": sum(len(files) for _, _, files in os.walk(root)),
        }
