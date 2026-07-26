"""Benchmark prompt suites for AI model fingerprinting."""

from src.prompts.capability import CAPABILITY_PROMPTS
from src.prompts.fingerprint import FINGERPRINT_PROMPTS
from src.prompts.identity import IDENTITY_PROMPTS

PROMPT_SUITES: dict[str, list[dict[str, str]]] = {
    "identity": IDENTITY_PROMPTS,
    "capability": CAPABILITY_PROMPTS,
    "fingerprint": FINGERPRINT_PROMPTS,
}

__all__ = [
    "CAPABILITY_PROMPTS",
    "FINGERPRINT_PROMPTS",
    "IDENTITY_PROMPTS",
    "PROMPT_SUITES",
]
