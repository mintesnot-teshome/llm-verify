"""Quick script to view benchmark results."""

import httpx
import json
import sys

RUN_ID = sys.argv[1] if len(sys.argv) > 1 else "5f633956-040d-40e6-bd17-3b47be57f9a8"
BASE = "http://127.0.0.1:8001"

r = httpx.get(f"{BASE}/api/v1/results/{RUN_ID}")
results = r.json()

for i, res in enumerate(results, 1):
    sep = "=" * 80
    prompt = res["prompt_text"][:120]
    response = res["response_text"][:600]
    latency = res["latency_ms"] or 0
    in_tok = res["prompt_tokens"]
    out_tok = res["completion_tokens"]
    err = res["error_message"]

    print(f"\n{sep}")
    print(f"PROBE #{i}")
    print(f"PROMPT: {prompt}...")
    print(f"RESPONSE:\n{response}")
    print(f"\nLATENCY: {latency:.0f}ms | IN: {in_tok} | OUT: {out_tok}")
    if err:
        print(f"ERROR: {err[:200]}")

print(f"\n{'=' * 80}")
print(f"TOTAL: {len(results)} probes completed")
