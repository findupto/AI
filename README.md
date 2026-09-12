# Findupto AI — Standalone Local AI

A self-hosted desktop AI foundation derived from the supplied architecture roadmaps.

## What this build provides
- Local-first chat UI with no mandatory remote AI API
- Configurable GGUF model support through `llama-cpp-python`
- Orchestrator layer for routing, context, memory, retrieval and tools
- Local SQLite knowledge store with FTS5 search and provenance
- Local document ingestion for TXT, Markdown, JSON and PDF text extraction
- Sandboxed Python tool with timeout and restricted environment
- Optional web research hook, disabled by default
- Persistent conversation history and basic memory
- Windows-friendly launcher and cross-platform Python entry point
- Clear extension points for vision, image/video, audio, fine-tuning and evaluation

## Reality boundary
This repository is the software foundation, not a pre-trained frontier model. The supplied PDFs explicitly recommend starting from a strong open-weight model and adding orchestration, retrieval, tools, multimodality, evaluation and controlled learning rather than attempting frontier pre-training from scratch.

## Quick start
1. Install Python 3.11+.
2. Install dependencies: `python -m pip install -e .`
3. Put a compatible GGUF model in `models/` (or set `FINDUPTO_MODEL_PATH`).
4. Run `python run.py` on Windows, Linux or macOS.
5. For Windows, double-click `Start_AI.bat`.

The application can run fully offline when a local model and local knowledge are used. Network research is an explicit optional capability.

## Project structure
```text
apps/                 Desktop application
orchestrator/         Agent loop, routing, memory and permissions
models/               Local model adapters
knowledge/             Ingestion, retrieval and provenance
memory/                SQLite conversation memory
tools/                 Sandboxed local tools
security/              Policy gates
evaluation/            Regression/evaluation hooks
infra/                 Packaging/deployment helpers
tests/                 Automated tests
```

See `config/default.json` for runtime settings.