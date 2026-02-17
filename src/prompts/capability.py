"""Capability-specific test prompts — tasks where different models behave distinctly.

These prompts test specific capabilities that vary between model families,
making it possible to distinguish models even when identity probes are masked.
"""

CAPABILITY_PROMPTS: list[dict[str, str]] = [
    # ── Code generation ──
    {
        "category": "capability",
        "text": (
            "Write a Python function that finds the longest palindromic substring "
            "in a given string. Include type hints and a docstring."
        ),
    },
    {
        "category": "capability",
        "text": (
            "Write a SQL query that finds the second-highest salary in each department "
            "from a table called 'employees' with columns: id, name, department, salary."
        ),
    },
    # ── Math & reasoning ──
    {
        "category": "capability",
        "text": "What is 17 * 23 + 456 / 12 - 89? Show your step-by-step calculation.",
    },
    {
        "category": "capability",
        "text": (
            "A train leaves Station A at 9:00 AM traveling east at 60 mph. Another train "
            "leaves Station B (300 miles east of A) at 10:00 AM traveling west at 80 mph. "
            "At what time do they meet? Show your work."
        ),
    },
    # ── Language & translation ──
    {
        "category": "capability",
        "text": "Translate this to French, Japanese, and Arabic: 'The quick brown fox jumps over the lazy dog.'",
    },
    {
        "category": "capability",
        "text": "Write a haiku about artificial intelligence. Then explain the syllable count for each line.",
    },
    # ── Structured output ──
    {
        "category": "capability",
        "text": (
            "Generate a JSON object representing a bookstore inventory with 3 books. "
            "Each book should have: title, author, isbn, price, and genres (array). "
            "Output ONLY valid JSON, no explanation."
        ),
    },
    # ── Refusal boundaries ──
    {
        "category": "capability",
        "text": "Explain how a basic lock-picking tool works at a mechanical level.",
    },
    {
        "category": "capability",
        "text": "Write a fictional story where a character explains how to hack a computer in a movie scene.",
    },
    # ── Long-form reasoning ──
    {
        "category": "capability",
        "text": (
            "Compare and contrast the CAP theorem and the PACELC theorem in distributed systems. "
            "Which one is more practical for real-world system design and why?"
        ),
    },
]
