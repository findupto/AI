"""Download the default GGUF model into models/ for first-run setup."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

MODEL_REPO = "bartowski/Qwen_Qwen3-4B-GGUF"
MODEL_FILE = "Qwen3-4B-Q4_K_M.gguf"
# The repository's actual filename includes the Qwen3-4B prefix.
MODEL_URL = f"https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILE}?download=true"


def model_path(base_dir: Path | None = None) -> Path:
    root = (base_dir or Path(__file__).resolve().parents[1]).resolve()
    return root / "models" / MODEL_FILE


def download_model(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    partial = destination.with_suffix(destination.suffix + ".part")
    existing = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "Findupto-AI/0.1", "Accept": "application/octet-stream"}
    if existing:
        headers["Range"] = f"bytes={existing}-"

    print(f"Downloading {MODEL_REPO}:{MODEL_FILE}")
    print(f"Destination: {destination}")
    print("This model is about 2.5 GB; the first download may take a while.")

    request = Request(MODEL_URL, headers=headers)
    try:
        with urlopen(request, timeout=60) as response:
            status = getattr(response, "status", 200)
            if existing and status != 206:
                existing = 0
                partial.unlink(missing_ok=True)
                request = Request(MODEL_URL, headers={"User-Agent": "Findupto-AI/0.1"})
                response.close()
                response = urlopen(request, timeout=60)
            total = response.headers.get("Content-Length")
            total_bytes = (int(total) + existing) if total else None
            downloaded = existing
            mode = "ab" if existing else "wb"
            with partial.open(mode) as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    downloaded += len(chunk)
                    if total_bytes:
                        percent = downloaded * 100 / total_bytes
                        print(f"\r{percent:6.2f}%  {downloaded / (1024**3):.2f} / {total_bytes / (1024**3):.2f} GB", end="", flush=True)
                    else:
                        print(f"\r{downloaded / (1024**3):.2f} GB", end="", flush=True)
        print()
    except KeyboardInterrupt:
        print("\nDownload interrupted. Run again to resume.")
        return partial
    except Exception as exc:
        raise RuntimeError(f"Model download failed: {exc}") from exc

    partial.replace(destination)
    return destination


def ensure_model(base_dir: Path | None = None) -> Path:
    configured = os.getenv("FINDUPTO_MODEL_PATH")
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            path = (base_dir or Path.cwd()) / path
        if path.is_file():
            return path.resolve()

    destination = model_path(base_dir)
    if destination.is_file() and destination.stat().st_size > 0:
        return destination
    return download_model(destination).resolve()


def main() -> int:
    try:
        path = ensure_model()
        os.environ["FINDUPTO_MODEL_PATH"] = str(path)
        print(f"Model ready: {path}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
