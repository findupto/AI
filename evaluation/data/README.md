# Evaluation datasets

This directory contains small deterministic datasets for local smoke checks.

Run the bundled benchmark with:

```bash
findupto-benchmark evaluation/data/smoke_cases.json
findupto-benchmark evaluation/data/quality_cases.json
```

The smoke dataset intentionally contains one passing and one failing case so the evaluator's reporting behavior is visible. The quality dataset contains two passing examples covering local-model and source-aware responses.
