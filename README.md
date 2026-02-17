# 🔍 LLM Verify — AI Model Fraud Detector & LLM Fingerprinting Toolkit

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Detect fake AI APIs** — Verify if an LLM API is actually serving the model it claims. Catch resellers who sell you "Claude" or "ChatGPT" but secretly serve Kimi, LLaMA, or other cheaper models behind a system prompt.

## The Problem

AI API resellers are committing **model fraud**: they sell access to premium models like Claude or ChatGPT, but behind the scenes, they use a cheaper model with a system prompt like _"You are Claude, made by Anthropic."_ You're paying premium prices for a knockoff.

**LLM Verify** catches this by running behavioral fingerprinting benchmarks — a suite of prompts designed to reveal a model's true identity through its response patterns, not just what it _says_ it is.

### Key Features

- 🧬 **Behavioral Fingerprinting** — Identify models by how they respond, not what they claim
- 🆚 **Side-by-Side Comparison** — Compare suspect APIs against verified baselines
- 🎯 **32 Forensic Prompts** — Identity probes, capability tests, and style analysis
- 📊 **Multi-Dimensional Scoring** — Latency, token usage, vocabulary, formatting patterns
- ⚡ **Async & Fast** — Concurrent API calls with configurable rate limiting
- 🔌 **Any OpenAI-Compatible API** — Works with any endpoint that speaks the OpenAI protocol

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Copy environment config
cp .env.example .env
# Edit .env with your API keys

# 4. Run the API server
uvicorn src.main:app --reload

# 5. Run tests
pytest
```

## API Endpoints

| Method | Endpoint                           | Description                        |
| ------ | ---------------------------------- | ---------------------------------- |
| GET    | `/health`                          | Health check                       |
| POST   | `/api/v1/benchmarks/`              | Start a new benchmark run          |
| GET    | `/api/v1/benchmarks/`              | List all benchmark runs            |
| GET    | `/api/v1/benchmarks/{id}`          | Get a specific benchmark run       |
| GET    | `/api/v1/results/{run_id}`         | Get results for a run              |
| POST   | `/api/v1/results/compare`          | Compare two runs (fraud detection) |
| GET    | `/api/v1/results/{id}/fingerprint` | Generate behavioral fingerprint    |

## How It Works

1. **Run benchmarks** against a trusted model (e.g., real Claude API) → baseline
2. **Run same benchmarks** against the suspect API
3. **Compare** the two runs — the system analyzes:
   - Response latency patterns
   - Response length & style
   - Token usage
   - Error rates
   - Vocabulary & formatting fingerprints
4. **Get verdict:** MATCH, MISMATCH, or INCONCLUSIVE

## Project Structure

```
src/
├── adapters/      # AI provider API clients (OpenAI, Anthropic, generic)
├── handlers/      # FastAPI route handlers
├── models/        # SQLAlchemy ORM models
├── prompts/       # Benchmark prompt suites (identity, capability, fingerprint)
├── repositories/  # Database access layer
├── schemas/       # Pydantic request/response models
├── services/      # Business logic (runner, comparator, fingerprinting)
├── config.py      # Centralized settings
├── database.py    # Async SQLAlchemy setup
└── main.py        # FastAPI app entry point
```

## License

MIT
