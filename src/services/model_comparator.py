"""Model comparator service — compares benchmark results between two runs."""

import logging
import statistics

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.result import BenchmarkResult
from src.repositories.result_repo import ResultRepository
from src.schemas.result import ComparisonRequest, ComparisonScore

logger = logging.getLogger(__name__)


class ModelComparatorService:
    """Compares benchmark results between a baseline and suspect run."""

    def __init__(self, session: AsyncSession) -> None:
        self._result_repo = ResultRepository(session)

    async def compare(self, request: ComparisonRequest) -> ComparisonScore:
        """Compare two benchmark runs and produce a similarity score.

        Args:
            request: Contains baseline and suspect run IDs.

        Returns:
            ComparisonScore with overall similarity and per-dimension breakdown.
        """
        baseline = await self._result_repo.get_by_run_id(request.baseline_run_id)
        suspect = await self._result_repo.get_by_run_id(request.suspect_run_id)

        if not baseline or not suspect:
            return self._inconclusive("One or both runs have no results.")

        dimensions = self._compute_dimensions(baseline, suspect)
        overall = self._compute_overall(dimensions)
        verdict = self._determine_verdict(overall)

        return ComparisonScore(
            baseline_run_id=request.baseline_run_id,
            suspect_run_id=request.suspect_run_id,
            overall_similarity=round(overall, 4),
            dimensions=dimensions,
            verdict=verdict,
            details=self._build_details(dimensions, verdict),
        )

    def _compute_dimensions(
        self,
        baseline: list[BenchmarkResult],
        suspect: list[BenchmarkResult],
    ) -> dict[str, float]:
        """Compute similarity across multiple dimensions.

        Args:
            baseline: Results from the trusted baseline run.
            suspect: Results from the suspect run.

        Returns:
            Dictionary mapping dimension names to similarity scores (0.0-1.0).
        """
        return {
            "latency": self._compare_latency(baseline, suspect),
            "response_length": self._compare_response_length(baseline, suspect),
            "token_usage": self._compare_token_usage(baseline, suspect),
            "error_rate": self._compare_error_rates(baseline, suspect),
        }

    def _compare_latency(
        self,
        baseline: list[BenchmarkResult],
        suspect: list[BenchmarkResult],
    ) -> float:
        """Compare latency distributions between two result sets.

        Args:
            baseline: Baseline results.
            suspect: Suspect results.

        Returns:
            Similarity score (0.0-1.0).
        """
        b_latencies = [r.latency_ms for r in baseline if r.latency_ms is not None]
        s_latencies = [r.latency_ms for r in suspect if r.latency_ms is not None]

        if not b_latencies or not s_latencies:
            return 0.5  # Inconclusive

        b_mean = statistics.mean(b_latencies)
        s_mean = statistics.mean(s_latencies)
        max_mean = max(b_mean, s_mean, 1.0)

        return 1.0 - abs(b_mean - s_mean) / max_mean

    def _compare_response_length(
        self,
        baseline: list[BenchmarkResult],
        suspect: list[BenchmarkResult],
    ) -> float:
        """Compare average response lengths.

        Args:
            baseline: Baseline results.
            suspect: Suspect results.

        Returns:
            Similarity score (0.0-1.0).
        """
        b_lengths = [len(r.response_text) for r in baseline if r.response_text]
        s_lengths = [len(r.response_text) for r in suspect if r.response_text]

        if not b_lengths or not s_lengths:
            return 0.5

        b_mean = statistics.mean(b_lengths)
        s_mean = statistics.mean(s_lengths)
        max_mean = max(b_mean, s_mean, 1.0)

        return 1.0 - abs(b_mean - s_mean) / max_mean

    def _compare_token_usage(
        self,
        baseline: list[BenchmarkResult],
        suspect: list[BenchmarkResult],
    ) -> float:
        """Compare token usage patterns.

        Args:
            baseline: Baseline results.
            suspect: Suspect results.

        Returns:
            Similarity score (0.0-1.0).
        """
        b_tokens = [r.total_tokens for r in baseline if r.total_tokens is not None]
        s_tokens = [r.total_tokens for r in suspect if r.total_tokens is not None]

        if not b_tokens or not s_tokens:
            return 0.5

        b_mean = statistics.mean(b_tokens)
        s_mean = statistics.mean(s_tokens)
        max_mean = max(b_mean, s_mean, 1.0)

        return 1.0 - abs(b_mean - s_mean) / max_mean

    def _compare_error_rates(
        self,
        baseline: list[BenchmarkResult],
        suspect: list[BenchmarkResult],
    ) -> float:
        """Compare error rates between two result sets.

        Args:
            baseline: Baseline results.
            suspect: Suspect results.

        Returns:
            Similarity score (0.0-1.0). 1.0 means same error rate.
        """
        b_error_rate = _error_rate(baseline)
        s_error_rate = _error_rate(suspect)

        return 1.0 - abs(b_error_rate - s_error_rate)

    def _compute_overall(self, dimensions: dict[str, float]) -> float:
        """Compute weighted overall similarity from dimension scores.

        Args:
            dimensions: Per-dimension similarity scores.

        Returns:
            Overall similarity (0.0-1.0).
        """
        weights = {
            "latency": 0.15,
            "response_length": 0.30,
            "token_usage": 0.25,
            "error_rate": 0.30,
        }
        total_weight = sum(weights.get(key, 0.0) for key in dimensions)
        if total_weight == 0:
            return 0.5

        weighted_sum = sum(
            score * weights.get(key, 0.0)
            for key, score in dimensions.items()
        )
        return weighted_sum / total_weight

    def _determine_verdict(self, overall: float) -> str:
        """Determine the verdict based on overall similarity.

        Args:
            overall: The overall similarity score.

        Returns:
            MATCH, MISMATCH, or INCONCLUSIVE.
        """
        if overall >= 0.80:
            return "MATCH"
        if overall <= 0.50:
            return "MISMATCH"
        return "INCONCLUSIVE"

    def _build_details(self, dimensions: dict[str, float], verdict: str) -> str:
        """Build a human-readable explanation of the comparison.

        Args:
            dimensions: Per-dimension similarity scores.
            verdict: The verdict string.

        Returns:
            A formatted explanation string.
        """
        lines = [f"Verdict: {verdict}", "Dimension scores:"]
        for key, score in sorted(dimensions.items()):
            lines.append(f"  {key}: {score:.2%}")
        return "\n".join(lines)

    def _inconclusive(self, reason: str) -> ComparisonScore:
        """Return an inconclusive comparison result.

        Args:
            reason: Why the comparison is inconclusive.

        Returns:
            A ComparisonScore with INCONCLUSIVE verdict.
        """
        return ComparisonScore(
            baseline_run_id="",
            suspect_run_id="",
            overall_similarity=0.5,
            dimensions={},
            verdict="INCONCLUSIVE",
            details=reason,
        )


def _error_rate(results: list[BenchmarkResult]) -> float:
    """Calculate the error rate for a list of results.

    Args:
        results: The benchmark results to analyze.

    Returns:
        Error rate as a float (0.0-1.0).
    """
    if not results:
        return 0.0
    errors = sum(1 for r in results if r.error_message)
    return errors / len(results)
