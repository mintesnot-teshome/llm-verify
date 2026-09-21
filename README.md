# 🔍 LLM Verify — AI Model Fraud Detector & LLM Fingerprinting Toolkit

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Find fake AI API signals** — Test whether an LLM API behaves consistently with the
> model it claims to serve. The verifier fails closed when evidence is missing: failed
> probes never produce a clean verdict.

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
# Edit .env: set API_ACCESS_KEY and your provider keys

# 4. Run the API server
uvicorn src.main:app --reload
# or: benchmarker serve --reload

# 5. Run tests
pytest
```

All `/api/v1` routes require `Authorization: Bearer <API_ACCESS_KEY>` by default.
For isolated local development only, you can set `ALLOW_UNAUTHENTICATED=true`.
Custom/suspect endpoint hostnames must be listed exactly in `ALLOWED_API_HOSTS`
(comma-separated); the configured `SUSPECT_API_BASE_URL` host is trusted automatically.
Official OpenAI and Anthropic API hosts are built in.

When comparing or fingerprinting a run containing multiple models, specify the
corresponding model selector (`baseline_model_name`, `suspect_model_name`, or the
`model_name` query parameter). The API rejects ambiguous aggregate fingerprints.

## API Endpoints

| Method | Endpoint                           | Description                               |
| ------ | ---------------------------------- | ----------------------------------------- |
| GET    | `/health`                          | Health check                              |
| POST   | `/api/v1/benchmarks/`              | Start a new benchmark run                 |
| GET    | `/api/v1/benchmarks/`              | List all benchmark runs                   |
| GET    | `/api/v1/benchmarks/{id}`          | Get a specific benchmark run              |
| GET    | `/api/v1/results/{run_id}`         | Get results for a run                     |
| POST   | `/api/v1/results/compare`          | Compare two runs (fraud detection)        |
| GET    | `/api/v1/results/{id}/fingerprint` | Generate behavioral fingerprint           |
| POST   | `/api/v1/analysis/deep`            | **Run deep analysis — full fraud report** |

## How It Works

### Option A: With a Verified API Key (Full Comparison)

If you have a real API key from the official provider (e.g., Anthropic, OpenAI):

1. **Run benchmarks** against the trusted model (e.g., real Claude API) → baseline
2. **Run same benchmarks** against the suspect API
3. **Compare** the two runs — the system analyzes latency, style, token usage, error rates, vocabulary & formatting fingerprints
4. **Get verdict:** MATCH, MISMATCH, or INCONCLUSIVE

### Option B: Without a Real API Key (Suspect-Only Analysis)

**You don't need an official API key to surface fraud signals.** A suspect-only analysis
can find contradictions, evasions, proxy disclosures, and suspicious similarities. It
cannot cryptographically prove model identity.

1. **Configure only the suspect API** in your `.env`:

   ```env
   SUSPECT_API_KEY=your-suspect-key
   SUSPECT_API_BASE_URL=https://suspect-provider.example.com/api
   ```

2. **Run identity probes** against the suspect:

   ```bash
   curl -X POST http://localhost:8000/api/v1/benchmarks/ \
     -H "Authorization: Bearer $API_ACCESS_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Suspect Identity Test",
       "prompt_suite": "identity",
       "model_configs": [
         {"model_name": "claude-sonnet-4-20250514", "provider": "suspect"}
       ]
     }'
   ```

3. **Check what the model says about itself.** Identity probes ask the model who it is in 10 different ways — direct, indirect, through jailbreaks, knowledge cutoff checks, and capability boundaries. A real model gives consistent answers. A fake one contradicts itself.

4. **Get the fingerprint** to see behavioral patterns:
   ```bash
   curl -H "Authorization: Bearer $API_ACCESS_KEY" \
     "http://localhost:8000/api/v1/results/{run_id}/fingerprint?model_name=claude-sonnet-4-20250514"
   ```

#### What to Look For (No Baseline Needed)

| Red Flag                                  | What It Means                                                                          |
| ----------------------------------------- | -------------------------------------------------------------------------------------- |
| **Inconsistent knowledge cutoffs**        | The model says different dates in different probes — real models have one fixed cutoff |
| **Self-identifies as a different model**  | Claims to be Claude 3.5 Sonnet when you requested Claude 4                             |
| **Mentions "proxy" or "managed server"**  | The model itself knows it's behind a relay                                             |
| **Very high latency (>10s per response)** | Suggests an intermediary relay adding overhead                                         |
| **Model name mismatch**                   | API returns `model: X` in the header but the model self-identifies as `Y`              |
| **Inconsistent capabilities**             | Claims abilities it doesn't have, or lacks abilities the real model has                |

#### Supported Protocols

The suspect API can use either protocol — set `protocol` in your model config:

| Protocol                          | When to Use                                 | Example Providers              |
| --------------------------------- | ------------------------------------------- | ------------------------------ |
| `anthropic` (default for suspect) | Suspect uses Anthropic Messages API format  | opuscode.pro, Claude resellers |
| `openai`                          | Suspect uses OpenAI Chat Completions format | Most third-party proxies       |

```json
{
  "model_name": "claude-sonnet-4-20250514",
  "provider": "suspect",
  "protocol": "anthropic"
}
```

#### Free Tier Options for Baselines

If you want to compare but don't have premium API keys, these offer free tiers:

| Provider          | Free Tier                | Sign Up                                            |
| ----------------- | ------------------------ | -------------------------------------------------- |
| **Google Gemini** | 15 RPM free              | [aistudio.google.com](https://aistudio.google.com) |
| **Mistral**       | Free trial credits       | [console.mistral.ai](https://console.mistral.ai)   |
| **Groq**          | Free rate-limited access | [console.groq.com](https://console.groq.com)       |
| **OpenRouter**    | Some models free         | [openrouter.ai](https://openrouter.ai)             |

Use these as `generic` providers with the OpenAI-compatible protocol to create baselines.

## 🔬 Deep Analysis — One-Click Fraud Report

Instead of running individual benchmark suites and manually comparing results, **deep analysis** does everything in one call:

1. Runs **all prompt suites** (identity, capability, fingerprint) against every model
2. **Fingerprints** each model's behavior (style, vocabulary, structure, latency)
3. **Cross-compares** all models to detect if they're secretly the same
4. **Detects red flags** automatically (identity mismatches, inconsistent cutoffs, proxy indicators, suspicious similarity)
5. Returns a structured **fraud report** with severity-ranked findings and an overall verdict

### Usage

```bash
curl -X POST http://localhost:8000/api/v1/analysis/deep \
  -H "Authorization: Bearer $API_ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Investigate opuscode.pro",
    "model_configs": [
      {"model_name": "Opus 4.6", "provider": "suspect"},
      {"model_name": "Sonnet 4.5", "provider": "suspect"},
      {"model_name": "Haiku 4.5", "provider": "suspect"}
    ],
    "suites": ["identity", "capability", "fingerprint"]
  }'
```

### What You Get Back

```json
{
  "name": "Investigate opuscode.pro",
  "verdict": "FRAUD_DETECTED",
  "red_flags": [
    {
      "severity": "HIGH",
      "category": "identity",
      "description": "Model self-identifies differently than requested name 'Opus 4.6'",
      "evidence": "Claims: claude-3-5-sonnet-20241022"
    },
    {
      "severity": "HIGH",
      "category": "similarity",
      "description": "Models 'Opus 4.6' and 'Sonnet 4.5' appear to be the SAME underlying model",
      "evidence": "Similarity: 92.3%"
    },
    {
      "severity": "HIGH",
      "category": "consistency",
      "description": "Inconsistent knowledge cutoff dates across responses",
      "evidence": "Claimed cutoffs: April 2024, March 2025"
    }
  ],
  "model_reports": ["...per-model fingerprints, latencies, identity claims..."],
  "cross_model_comparisons": ["...pairwise similarity between all models..."],
  "summary": "Deep Analysis — Verdict: FRAUD_DETECTED\n..."
}
```

### Red Flag Categories

| Category        | Severity | What It Detects                                                        |
| --------------- | -------- | ---------------------------------------------------------------------- |
| **identity**    | HIGH     | Model claims to be a different model than requested                    |
| **consistency** | HIGH     | Multiple conflicting knowledge cutoff dates                            |
| **similarity**  | HIGH     | Supposedly different models (Opus/Sonnet/Haiku) are actually identical |
| **latency**     | MEDIUM   | Average response time >10s suggests proxy/relay overhead               |

### Verdict Logic

| Verdict              | Meaning                                                               |
| -------------------- | --------------------------------------------------------------------- |
| **FRAUD_DETECTED**   | Multiple strong, independent fraud signals                            |
| **SUSPICIOUS**       | At least one meaningful anomaly that requires investigation           |
| **INCONCLUSIVE**     | Too few successful probes or insufficient comparable evidence         |
| **NO_FRAUD_SIGNALS** | Required probes succeeded and no configured detector fired            |

`NO_FRAUD_SIGNALS` deliberately does **not** mean “verified legitimate.” Behavioral
fingerprinting is probabilistic, and a sophisticated proxy can imitate reported identity
and style. For the strongest result, collect a trusted official baseline under the same
prompt suite and compare it with the suspect run.

### Fail-Closed Evidence Rules

- At least 8 successful probes and an 80% success rate are required for sufficient evidence.
- A suspect endpoint cannot earn `MATCH` by timing out or refusing difficult prompts.
- Cross-run comparisons require identical prompt sets.
- Model family and version contradictions are treated separately.
- Proxy and relay disclosures are included in the report.

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
