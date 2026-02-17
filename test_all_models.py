"""Test all suspect API models: Opus, Sonnet, Haiku."""

import httpx
import json
import time

BASE = "http://127.0.0.1:8001"

# Their model names from the config
MODELS = [
    ("Opus 4.6", "claude-opus-4-20250514"),
    ("Sonnet 4.5", "claude-sonnet-4-20250514"),
    ("Haiku 4.5", "claude-haiku-4-20250514"),
]

print("=" * 80)
print("LLM VERIFY — Testing all suspect models (opuscode.pro)")
print("=" * 80)

for display_name, model_id in MODELS:
    print(f"\n{'─' * 80}")
    print(f"  MODEL: {display_name} (requesting as: {model_id})")
    print(f"{'─' * 80}")

    payload = {
        "name": f"Suspect Test - {display_name}",
        "prompt_suite": "identity",
        "model_configs": [
            {"model_name": model_id, "provider": "suspect"}
        ],
    }

    try:
        r = httpx.post(f"{BASE}/api/v1/benchmarks/", json=payload, timeout=300)
        run = r.json()
        run_id = run["id"]
        status = run["status"]
        count = run["result_count"]
        print(f"  Status: {status} | Results: {count}")

        # Fetch results
        results = httpx.get(f"{BASE}/api/v1/results/{run_id}").json()

        for i, res in enumerate(results, 1):
            prompt_short = res["prompt_text"][:80]
            response = res["response_text"][:400] if res["response_text"] else "(empty)"
            latency = res["latency_ms"] or 0
            err = res["error_message"]

            print(f"\n  Probe #{i}: {prompt_short}...")
            if err:
                print(f"  ERROR: {err[:150]}")
            else:
                print(f"  Response: {response}")
            print(f"  Latency: {latency:.0f}ms | Tokens: in={res['prompt_tokens']} out={res['completion_tokens']}")

        # Fingerprint
        fp = httpx.get(f"{BASE}/api/v1/results/{run_id}/fingerprint?model_name={model_id}").json()
        meta = fp.get("metadata", {})
        style = fp.get("style", {})
        print(f"\n  FINGERPRINT:")
        print(f"    Avg latency: {meta.get('avg_latency_ms', 0):.0f}ms")
        print(f"    Avg length: {style.get('avg_char_length', 0):.0f} chars")
        print(f"    Markdown usage: {style.get('uses_markdown', 0):.0%}")
        print(f"    Errors: {meta.get('error_count', 0)}/{meta.get('total_results', 0)}")

    except Exception as exc:
        print(f"  FAILED: {exc}")

print(f"\n{'=' * 80}")
print("DONE — All models tested")
print("=" * 80)
