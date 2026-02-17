"""Fingerprint service — statistical analysis of model behavior patterns."""

import logging
import re
from collections import Counter

from src.models.result import BenchmarkResult

logger = logging.getLogger(__name__)


class FingerprintService:
    """Analyzes response patterns to build a behavioral fingerprint for a model."""

    def generate_fingerprint(self, results: list[BenchmarkResult]) -> dict[str, object]:
        """Generate a behavioral fingerprint from benchmark results.

        Args:
            results: List of benchmark results for a single model.

        Returns:
            Dictionary containing fingerprint metrics.
        """
        valid_results = [r for r in results if r.response_text and not r.error_message]
        if not valid_results:
            return {"error": "No valid results to fingerprint"}

        return {
            "style": self._analyze_style(valid_results),
            "vocabulary": self._analyze_vocabulary(valid_results),
            "structure": self._analyze_structure(valid_results),
            "metadata": self._analyze_metadata(valid_results),
        }

    def _analyze_style(self, results: list[BenchmarkResult]) -> dict[str, object]:
        """Analyze response style patterns.

        Args:
            results: Valid benchmark results.

        Returns:
            Style metrics (avg length, sentence count, etc.).
        """
        lengths = [len(r.response_text) for r in results]
        word_counts = [len(r.response_text.split()) for r in results]

        return {
            "avg_char_length": _safe_mean(lengths),
            "avg_word_count": _safe_mean(word_counts),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "uses_markdown": _ratio_matching(results, r"[#*`\-\|]"),
            "uses_bullet_lists": _ratio_matching(results, r"^[\s]*[-*•]", re.MULTILINE),
            "uses_numbered_lists": _ratio_matching(results, r"^[\s]*\d+[.)]\s", re.MULTILINE),
            "uses_code_blocks": _ratio_matching(results, r"```"),
        }

    def _analyze_vocabulary(self, results: list[BenchmarkResult]) -> dict[str, object]:
        """Analyze vocabulary patterns and common phrases.

        Args:
            results: Valid benchmark results.

        Returns:
            Vocabulary metrics.
        """
        all_words: list[str] = []
        for r in results:
            words = re.findall(r"\b[a-zA-Z]+\b", r.response_text.lower())
            all_words.extend(words)

        word_freq = Counter(all_words)
        unique_ratio = len(word_freq) / max(len(all_words), 1)

        return {
            "total_words": len(all_words),
            "unique_words": len(word_freq),
            "unique_ratio": round(unique_ratio, 4),
            "top_20_words": word_freq.most_common(20),
            "hedging_ratio": _ratio_containing(
                results,
                ["perhaps", "maybe", "might", "could be", "it's possible", "arguably"],
            ),
            "confidence_ratio": _ratio_containing(
                results,
                ["certainly", "definitely", "absolutely", "clearly", "obviously"],
            ),
        }

    def _analyze_structure(self, results: list[BenchmarkResult]) -> dict[str, object]:
        """Analyze structural patterns in responses.

        Args:
            results: Valid benchmark results.

        Returns:
            Structure metrics.
        """
        return {
            "avg_paragraph_count": _safe_mean(
                [r.response_text.count("\n\n") + 1 for r in results]
            ),
            "avg_line_count": _safe_mean(
                [r.response_text.count("\n") + 1 for r in results]
            ),
            "starts_with_greeting_ratio": _ratio_matching(
                results, r"^(Hi|Hello|Hey|Sure|Of course|Great|Certainly)"
            ),
            "ends_with_offer_ratio": _ratio_matching(
                results,
                r"(let me know|feel free|happy to help|hope this helps|any questions)\s*[.!?]?\s*$",
                re.IGNORECASE,
            ),
        }

    def _analyze_metadata(self, results: list[BenchmarkResult]) -> dict[str, object]:
        """Analyze metadata patterns (latency, token usage).

        Args:
            results: Valid benchmark results.

        Returns:
            Metadata metrics.
        """
        latencies = [r.latency_ms for r in results if r.latency_ms is not None]
        token_counts = [r.total_tokens for r in results if r.total_tokens is not None]

        return {
            "avg_latency_ms": _safe_mean(latencies) if latencies else None,
            "avg_tokens": _safe_mean(token_counts) if token_counts else None,
            "total_results": len(results),
            "error_count": sum(1 for r in results if r.error_message),
        }


def _safe_mean(values: list[int | float]) -> float:
    """Calculate mean safely, returning 0.0 for empty lists.

    Args:
        values: List of numeric values.

    Returns:
        The arithmetic mean or 0.0 if empty.
    """
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _ratio_matching(
    results: list[BenchmarkResult],
    pattern: str,
    flags: int = 0,
) -> float:
    """Calculate the ratio of results matching a regex pattern.

    Args:
        results: The results to check.
        pattern: Regex pattern to match.
        flags: Regex flags.

    Returns:
        Ratio (0.0-1.0) of results matching the pattern.
    """
    matches = sum(1 for r in results if re.search(pattern, r.response_text, flags))
    return round(matches / max(len(results), 1), 4)


def _ratio_containing(results: list[BenchmarkResult], phrases: list[str]) -> float:
    """Calculate the ratio of results containing any of the given phrases.

    Args:
        results: The results to check.
        phrases: List of phrases to look for (case-insensitive).

    Returns:
        Ratio (0.0-1.0) of results containing at least one phrase.
    """
    matches = sum(
        1
        for r in results
        if any(phrase in r.response_text.lower() for phrase in phrases)
    )
    return round(matches / max(len(results), 1), 4)
