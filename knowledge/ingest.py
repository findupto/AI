from pathlib import Path


def read_document(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".txt", ".md", ".markdown", ".json", ".csv", ".py"}:
        return p.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(p)).pages)
    raise ValueError(f"Unsupported document type: {suffix}")
