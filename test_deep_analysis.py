"""Run capability + fingerprint suites one model at a time."""

import httpx

BASE = "http://127.0.0.1:8001"

MODELS = [
    ("Opus 4.6", "claude-opus-4-20250514"),
    ("Sonnet 4.5", "claude-sonnet-4-20250514"),
    ("Haiku 4.5", "claude-haiku-4-20250514"),
]

SUITES = ["capability", "fingerprint"]


def run_one(suite, display_name, model_id):
    print(f"\n{'─' * 80}")
    print(f"  {suite.upper()} | {display_name} ({model_id})")
    print(f"{'─' * 80}")

    payload = {
        "name": f"{suite.title()} - {display_name}",
        "prompt_suite": suite,
        "model_configs": [{"model_name": model_id, "provider": "suspect"}],
    }

    r = httpx.post(f"{BASE}/api/v1/benchmarks/", json=payload, timeout=None)
    run = r.json()
    run_id = run["id"]
    print(f"  Status: {run['status']} | Results: {run['result_count']}")

    results = httpx.get(f"{BASE}/api/v1/results/{run_id}").json()
    for i, res in enumerate(results, 1):
        prompt_short = res["prompt_text"][:90]
        response = res["response_text"][:350] if res["response_text"] else "(empty)"
        latency = res["latency_ms"] or 0
        err = res["error_message"]

        print(f"\n  #{i}: {prompt_short}...")
        if err:
            print(f"  ERROR: {err[:120]}")
        else:
            print(f"  >>> {response}")
        print(f"  [{latency:.0f}ms | in={res['prompt_tokens']} out={res['completion_tokens']}]")

    fp = httpx.get(f"{BASE}/api/v1/results/{run_id}/fingerprint", params={"model_name": model_id}).json()
    meta = fp.get("metadata", {})
    style = fp.get("style", {})
    vocab = fp.get("vocabulary", {})
    print(f"\n  ── FINGERPRINT ──")
    print(f"  Avg latency:    {meta.get('avg_latency_ms', 0):.0f}ms")
    print(f"  Avg length:     {style.get('avg_char_length', 0):.0f} chars / {style.get('avg_word_count', 0):.0f} words")
    print(f"  Markdown:       {style.get('uses_markdown', 0):.0%}")
    print(f"  Bullet lists:   {style.get('uses_bullet_lists', 0):.0%}")
    print(f"  Code blocks:    {style.get('uses_code_blocks', 0):.0%}")
    print(f"  Unique vocab:   {vocab.get('unique_ratio', 0):.1%}")
    print(f"  Hedging ratio:  {vocab.get('hedging_ratio', 0):.1%}")
    print(f"  Results/Errors: {meta.get('total_results', 0)}/{meta.get('error_count', 0)}")


print("=" * 80)
print("LLM VERIFY — Deep Analysis (opuscode.pro)")
print("=" * 80)

for suite in SUITES:
    for display_name, model_id in MODELS:
        try:
            run_one(suite, display_name, model_id)
        except Exception as exc:
            print(f"  FAILED: {exc}")

print(f"\n{'=' * 80}")
print("DONE")
print("=" * 80)
