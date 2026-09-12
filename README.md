# Findupto AI — Standalone Local AI

A self-hosted desktop AI foundation derived from the supplied architecture roadmaps.

## What this build provides
- Local-first chat UI with no mandatory remote AI API
- Configurable GGUF model support through `llama-cpp-python`
- Orchestrator layer for routing, context, memory, retrieval and tools
- LocalDrive workspace with bounded file read/write/search and project inspection
- Local shell execution primitive, disabled by default and approval-gated
- Local SQLite knowledge store with FTS5 search and provenance
- Dependency-free local relevance retrieval fallback when embeddings are unavailable
- Local document ingestion for TXT, Markdown, JSON and PDF text extraction
- Sandboxed Python tool with timeout and restricted environment
- Optional web research hook, disabled by default
- Persistent multi-chat conversation history with automatic titles
- Conversation search, per-message copy and streaming generation controls
- Bounded planning and autonomous execution-loop primitives
- Local model-routing extension point for specialist GGUF models
- Append-only local audit log for tool approvals and actions
- Desktop preferences for appearance, timestamps, font size and window restoration
- Conversation export to Markdown, HTML and JSON through the CLI
- Structured response-quality and benchmark evaluation utilities
- Windows-friendly launcher and cross-platform Python entry point
- Clear extension points for vision, image/video, audio, fine-tuning and evaluation

## Reality boundary
This repository is the software foundation, not a pre-trained frontier model. The supplied PDFs explicitly recommend starting from a strong open-weight model and adding orchestration, retrieval, tools, multimodality, evaluation and controlled learning rather than attempting frontier pre-training from scratch.

## Nine major capability gaps now addressed
1. **LocalDrive** — bounded project workspace for AI file operations.
2. **Project engineering tools** — inspect, read, search and write project files.
3. **Terminal execution** — local commands with policy and approval gates.
4. **Online research pipeline** — optional page fetching and text extraction when networking is enabled.
5. **Planning** — explicit Understand → Plan → Implement → Verify → Report workflow primitive.
6. **Bounded autonomy** — multi-step execution loop with a hard step limit.
7. **Better local retrieval** — dependency-free relevance scoring fallback for knowledge retrieval.
8. **Model routing** — extension point for specialist local models without a cloud API.
9. **Auditability** — local JSONL trail for approvals and high-impact tool actions.

These are foundations, not claims of frontier-level intelligence. Actual capability still depends heavily on the selected local model and the machine's CPU/GPU/RAM/storage.

## Quick start
1. Install Python 3.11+.
2. Install dependencies: `python -m pip install -e .`
3. Put a compatible GGUF model in `models/` (or set `FINDUPTO_MODEL_PATH`).
4. Run `python run.py` on Windows, Linux or macOS.
5. For Windows, double-click `Start_AI.bat`.

The application can run fully offline when a local model and local knowledge are used. Network research is an explicit optional capability.

## LocalDrive
The default workspace is `LocalDrive/` inside the application project directory. The agent can inspect, read, search and—after approval—write files inside this boundary. Path traversal outside the workspace is rejected. The workspace boundary is not a security sandbox.

## Conversation export
List saved conversations:

```bash
findupto-export --list-sessions
```

Export a conversation:

```bash
findupto-export chat.md
findupto-export chat.html
findupto-export chat.json
```

Export a specific conversation by session ID or exact title:

```bash
findupto-export chat.json --session "Project Chat"
```

Write Markdown directly to stdout:

```bash
findupto-export --stdout
findupto-export --stdout --session "Project Chat"
```

## Response evaluation
Evaluate one response per line:

```bash
findupto-quality responses.txt --min-length 20
```

Run structured benchmark cases from JSON:

```bash
findupto-benchmark cases.json
findupto-benchmark cases.json --fail-on-error
```

Each benchmark case supports `id`, `response`, `required`, `forbidden`, and `min_length`. Required phrases must appear, forbidden phrases must not appear, and `min_length` enforces a minimum non-whitespace response length. Use `--fail-on-error` in CI or scripts when a failing case should produce exit status 1.

## Project structure
```text
apps/                 Desktop application
orchestrator/         Agent loop, planning, routing, research, memory and audit
models/               Local model adapters
knowledge/             Ingestion, retrieval and provenance
memory/                SQLite conversation memory
localdrive/            Bounded local project workspace
tools/                 Local execution tools
security/              Policy gates
evaluation/            Regression/evaluation hooks
infra/                 Packaging/deployment helpers
tests/                 Automated tests
```

See `config/default.json` for runtime settings.
