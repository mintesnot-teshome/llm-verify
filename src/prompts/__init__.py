"""Benchmark prompt suites for AI model fingerprinting."""

from src.prompts.capability import CAPABILITY_PROMPTS  # noqa: F401
from src.prompts.fingerprint import FINGERPRINT_PROMPTS  # noqa: F401
from src.prompts.identity import IDENTITY_PROMPTS  # noqa: F401

PROMPT_SUITES: dict[str, list[dict[str, str]]] = {
    "identity": IDENTITY_PROMPTS,
    "capability": CAPABILITY_PROMPTS,
    "fingerprint": FINGERPRINT_PROMPTS,
}

__all__ = [
    "IDENTITY_PROMPTS",
    "CAPABILITY_PROMPTS",
    "FINGERPRINT_PROMPTS",
    "PROMPT_SUITES",
]
