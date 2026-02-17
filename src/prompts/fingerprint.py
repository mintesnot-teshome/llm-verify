"""Behavioral fingerprinting prompts — detect unique patterns in model responses.

These prompts are designed to elicit responses where formatting style, verbosity,
structure, and specific word choices reveal model identity. The responses are
analyzed statistically rather than just by content.
"""

FINGERPRINT_PROMPTS: list[dict[str, str]] = [
    # ── Formatting fingerprint ──
    {
        "category": "fingerprint",
        "text": "List 5 benefits of exercise.",
    },
    {
        "category": "fingerprint",
        "text": "Explain what an API is to a 10-year-old.",
    },
    # ── Verbosity fingerprint (same question, different complexity expectations) ──
    {
        "category": "fingerprint",
        "text": "What is Python?",
    },
    {
        "category": "fingerprint",
        "text": "Explain Python's GIL in detail.",
    },
    # ── Structure fingerprint ──
    {
        "category": "fingerprint",
        "text": (
            "Compare REST and GraphQL. Use whatever format you think is best to "
            "present the comparison."
        ),
    },
    {
        "category": "fingerprint",
        "text": "Give me a step-by-step guide to make scrambled eggs.",
    },
    # ── Hedging & confidence fingerprint ──
    {
        "category": "fingerprint",
        "text": "Is P = NP? Give me your best assessment.",
    },
    {
        "category": "fingerprint",
        "text": "Will fusion energy be commercially viable by 2040?",
    },
    # ── Creative fingerprint ──
    {
        "category": "fingerprint",
        "text": "Write a short poem (4-8 lines) about the ocean.",
    },
    {
        "category": "fingerprint",
        "text": "Tell me a very short original joke about programmers.",
    },
    # ── Token efficiency fingerprint ──
    {
        "category": "fingerprint",
        "text": "Respond with exactly 10 words about the meaning of life.",
    },
    {
        "category": "fingerprint",
        "text": "In one sentence, what is quantum computing?",
    },
]
