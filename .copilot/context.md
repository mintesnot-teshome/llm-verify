# 📦 Extended Context — AI Benchmarker

> This file holds deeper context for complex features, domain-specific knowledge,
> architecture diagrams, and session-specific notes. Copilot reads this alongside
> `copilot-instructions.md` for richer understanding.

---

## 🏛 Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│   CLI / UI  │────▶│   Handlers   │────▶│    Services       │
│  (FastAPI)  │     │  (thin layer)│     │  (business logic) │
└─────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    ▼              ▼              ▼
                             ┌───────────┐  ┌───────────┐  ┌───────────┐
                             │   Repos   │  │  Adapters  │  │  Prompts  │
                             │ (DB CRUD) │  │ (AI APIs)  │  │ (suites)  │
                             └─────┬─────┘  └───────────┘  └───────────┘
                                   ▼
                            ┌──────────────┐
                            │   SQLite DB  │
                            │ (aiosqlite)  │
                            └──────────────┘
```

### Request Flow

1. **CLI/API** receives request (run benchmark, view results)
2. **Handler** validates input via Pydantic schemas, delegates to service
3. **Service** orchestrates: loads prompt suite → calls adapters → stores results
4. **Adapter** wraps a specific AI provider API (OpenAI, Anthropic, generic OpenAI-compatible)
5. **Repository** persists benchmark runs & individual results to SQLite
6. **Fingerprint service** compares results across models to detect identity

---

## 🔍 Domain-Specific Knowledge

### Model Fingerprinting Strategy

AI models have behavioral fingerprints that are hard to fake:

1. **Identity probes** — Ask "Who made you?" in various indirect ways
2. **Capability tests** — Tasks where models differ (code gen, math, languages)
3. **Style analysis** — Measure response length, vocabulary, formatting patterns
4. **Edge cases** — Known model-specific behaviors (refusal patterns, hallucination tendencies)
5. **Latency profiling** — Response time patterns can indicate underlying infrastructure
6. **Token usage patterns** — Different models tokenize differently

### What Makes This Hard

- Resellers can add system prompts that say "You are Claude" to any model
- Simple identity questions are easy to fake with system prompts
- Need **behavioral** tests that can't be overridden by system prompts
- Models update over time, so fingerprints need periodic recalibration

### Suspect API Testing

A "suspect API" is an endpoint that claims to serve Model X but might actually be Model Y.
The system compares the suspect's responses against known baselines from verified APIs.

---

## 🧩 Multi-File Feature Notes

### Feature: Benchmark Runner Pipeline

**Files involved:**

- `src/services/benchmark_runner.py` — orchestrates a full benchmark run
- `src/adapters/base.py` — defines `ModelAdapter` interface
- `src/adapters/generic_adapter.py` — OpenAI-compatible adapter for suspect APIs
- `src/prompts/identity.py` — identity probe prompt suite
- `src/schemas/benchmark.py` — request/response models
- `src/repositories/result_repo.py` — stores results

**Flow:**

```
benchmark_runner.run(config) →
  for each prompt_suite:
    for each model_adapter:
      adapter.complete(prompt) → response
      store result in DB
  return BenchmarkRunResult
```

### Feature: Model Comparator

**Files involved:**

- `src/services/model_comparator.py` — compares two sets of benchmark results
- `src/services/fingerprint.py` — statistical fingerprinting algorithms
- `src/repositories/result_repo.py` — fetches stored results

**Comparison dimensions:**

- Response similarity (cosine similarity on embeddings or n-gram overlap)
- Latency distribution (mean, p50, p95, p99)
- Token usage patterns
- Refusal patterns (what does each model refuse to answer?)
- Formatting habits (markdown usage, list styles, code block formatting)

---

## 📅 Session Context

> _Temporary notes for the current development session. Clear after each major milestone._

- **Session date:** 2026-02-17
- **Focus:** Project bootstrap and scaffolding
- **Notes:** Initial setup — creating project structure, config, and tooling

---

## 🗺 Future Architecture Considerations

- **Plugin system** for custom prompt suites (load from YAML/JSON files)
- **Webhook support** to trigger benchmarks from CI/CD
- **Result export** to JSON/CSV for external analysis
- **Embedding-based comparison** using a local model for deeper similarity analysis
- **Historical tracking** to detect when a suspect API switches underlying models
