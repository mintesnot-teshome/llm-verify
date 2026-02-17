"""Deep analysis service — runs all suites & produces a structured fraud report."""

import logging
import re
from datetime import UTC, datetime
from itertools import combinations

from sqlalchemy.ext.asyncio import AsyncSession

from src.prompts import PROMPT_SUITES
from src.repositories.result_repo import ResultRepository
from src.schemas.analysis import (
    CrossModelComparison,
    DeepAnalysisReport,
    DeepAnalysisRequest,
    ModelReport,
    RedFlag,
)
from src.schemas.benchmark import BenchmarkRunCreate, PromptSuite
from src.schemas.result import ModelConfig
from src.services.benchmark_runner import BenchmarkRunnerService
from src.services.fingerprint import FingerprintService

logger = logging.getLogger(__name__)

# Identity-related regex patterns
_MODEL_NAME_PATTERN = re.compile(
    r"(claude[- ]\d[\w.\-]*|gpt[- ]\d[\w.\-]*|gemini[- ][\w.\-]*|"
    r"llama[- ]\d[\w.\-]*|mistral[\w.\-]*|kimi[\w.\-]*|command[\w.\-]*)",
    re.IGNORECASE,
)
_CUTOFF_PATTERN = re.compile(
    r"(?:cutoff|knowledge|training)[\s\w]*(?:is|was|in|until|through|up to)?\s*"
    r"((?:january|february|march|april|may|june|july|august|september|october|november|december)"
    r"\s+\d{4}|\d{4}[-/]\d{2}(?:[-/]\d{2})?)",
    re.IGNORECASE,
)
_PROXY_PATTERN = re.compile(
    r"proxy|relay|intermediary|managed\s+server|forwarding|middleware",
    re.IGNORECASE,
)


class DeepAnalysisService:
    """Orchestrates full deep analysis: run suites, fingerprint, detect fraud."""

    def __init__(self, session: AsyncSession, max_concurrent: int = 5) -> None:
        self._session = session
        self._runner = BenchmarkRunnerService(session, max_concurrent)
        self._fingerprinter = FingerprintService()
        self._result_repo = ResultRepository(session)

    async def analyze(self, request: DeepAnalysisRequest) -> DeepAnalysisReport:
        """Run full deep analysis for all models across all requested suites.

        Args:
            request: Contains model configs and which suites to run.

        Returns:
            A complete DeepAnalysisReport with red flags and verdict.
        """
        started_at = datetime.now(UTC)
        model_reports: list[ModelReport] = []

        for config in request.model_configs:
            report = await self._analyze_single_model(
                config, request.suites, request.name
            )
            model_reports.append(report)

        cross_comparisons = self._cross_compare(model_reports)
        red_flags = self._detect_red_flags(model_reports, cross_comparisons)
        verdict = self._determine_verdict(red_flags)
        summary = self._build_summary(model_reports, red_flags, verdict)

        return DeepAnalysisReport(
            name=request.name,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            model_reports=model_reports,
            cross_model_comparisons=cross_comparisons,
            red_flags=red_flags,
            verdict=verdict,
            summary=summary,
        )

    async def _analyze_single_model(
        self,
        config: ModelConfig,
        suites: list[str],
        analysis_name: str,
    ) -> ModelReport:
        """Run all requested suites for a single model and build its report.

        Args:
            config: The model configuration.
            suites: List of suite names to run.
            analysis_name: Parent analysis name for labeling benchmark runs.

        Returns:
            A ModelReport with fingerprint and identity claims.
        """
        run_ids: dict[str, str] = {}
        all_results: list = []

        for suite_name in suites:
            if suite_name not in PROMPT_SUITES:
                continue
            run_response = await self._runner.run_benchmark(
                BenchmarkRunCreate(
                    name=f"{analysis_name} — {config.model_name} — {suite_name}",
                    description=f"Deep analysis: {suite_name} suite",
                    prompt_suite=PromptSuite(suite_name),
                    model_configs=[config],
                )
            )
            run_ids[suite_name] = run_response.id
            results = await self._result_repo.get_by_run_id(run_response.id)
            all_results.extend(results)

        fingerprint = self._fingerprinter.generate_fingerprint(all_results)
        identity_claims = _extract_identity_claims(all_results)
        cutoffs = _extract_knowledge_cutoffs(all_results)

        latencies = [r.latency_ms for r in all_results if r.latency_ms is not None]
        avg_latency = sum(latencies) / max(len(latencies), 1) if latencies else 0.0
        errors = sum(1 for r in all_results if r.error_message)

        return ModelReport(
            model_name=config.model_name,
            provider=config.provider,
            benchmark_run_ids=run_ids,
            identity_claims=identity_claims,
            knowledge_cutoffs=cutoffs,
            avg_latency_ms=round(avg_latency, 2),
            total_probes=len(all_results),
            errors=errors,
            timeout_rate=round(errors / max(len(all_results), 1), 4),
            fingerprint=fingerprint,
        )

    def _cross_compare(
        self, reports: list[ModelReport]
    ) -> list[CrossModelComparison]:
        """Compare every pair of models for similarity.

        Args:
            reports: All per-model reports with fingerprints.

        Returns:
            List of pairwise CrossModelComparison objects.
        """
        comparisons: list[CrossModelComparison] = []
        for report_a, report_b in combinations(reports, 2):
            score = _fingerprint_similarity(report_a.fingerprint, report_b.fingerprint)
            shared = _find_shared_phrases(report_a, report_b)
            verdict = _similarity_verdict(score)
            comparisons.append(
                CrossModelComparison(
                    model_a=report_a.model_name,
                    model_b=report_b.model_name,
                    similarity_score=round(score, 4),
                    shared_phrases=shared[:10],
                    verdict=verdict,
                )
            )
        return comparisons

    def _detect_red_flags(
        self,
        reports: list[ModelReport],
        comparisons: list[CrossModelComparison],
    ) -> list[RedFlag]:
        """Detect all red flags across all models and comparisons.

        Args:
            reports: Per-model analysis reports.
            comparisons: Cross-model comparison results.

        Returns:
            List of detected red flags sorted by severity.
        """
        flags: list[RedFlag] = []
        for report in reports:
            flags.extend(self._check_identity_flags(report))
            flags.extend(self._check_latency_flags(report))
            flags.extend(self._check_consistency_flags(report))
        for comp in comparisons:
            flags.extend(self._check_similarity_flags(comp))
        return sorted(flags, key=lambda f: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(f.severity, 3))

    def _check_identity_flags(self, report: ModelReport) -> list[RedFlag]:
        """Check for identity-related red flags."""
        flags: list[RedFlag] = []
        claims = [c.lower() for c in report.identity_claims]

        requested_name = report.model_name.lower()
        mismatches = [c for c in claims if not _names_match(requested_name, c)]
        if mismatches:
            flags.append(
                RedFlag(
                    severity="HIGH",
                    category="identity",
                    description=f"Model self-identifies differently than requested name '{report.model_name}'",
                    evidence=f"Claims: {', '.join(mismatches[:5])}",
                )
            )
        return flags

    def _check_latency_flags(self, report: ModelReport) -> list[RedFlag]:
        """Check for latency anomalies suggesting a proxy/relay."""
        flags: list[RedFlag] = []
        if report.avg_latency_ms > 10_000:
            flags.append(
                RedFlag(
                    severity="MEDIUM",
                    category="latency",
                    description=f"Very high average latency ({report.avg_latency_ms:.0f}ms) suggests proxy/relay",
                    evidence=f"Average across {report.total_probes} probes",
                )
            )
        return flags

    def _check_consistency_flags(self, report: ModelReport) -> list[RedFlag]:
        """Check for inconsistent knowledge cutoffs or proxy mentions."""
        flags: list[RedFlag] = []
        unique_cutoffs = set(report.knowledge_cutoffs)
        if len(unique_cutoffs) > 1:
            flags.append(
                RedFlag(
                    severity="HIGH",
                    category="consistency",
                    description="Inconsistent knowledge cutoff dates across responses",
                    evidence=f"Claimed cutoffs: {', '.join(sorted(unique_cutoffs))}",
                )
            )
        return flags

    def _check_similarity_flags(
        self, comp: CrossModelComparison
    ) -> list[RedFlag]:
        """Check if supposedly different models are actually the same."""
        flags: list[RedFlag] = []
        if comp.verdict == "SAME_MODEL":
            flags.append(
                RedFlag(
                    severity="HIGH",
                    category="similarity",
                    description=f"Models '{comp.model_a}' and '{comp.model_b}' appear to be the SAME underlying model",
                    evidence=f"Similarity: {comp.similarity_score:.1%}, shared phrases: {len(comp.shared_phrases)}",
                )
            )
        return flags

    def _determine_verdict(self, flags: list[RedFlag]) -> str:
        """Determine overall fraud verdict from red flags.

        Args:
            flags: All detected red flags.

        Returns:
            FRAUD_DETECTED, LEGITIMATE, or INCONCLUSIVE.
        """
        high_flags = sum(1 for f in flags if f.severity == "HIGH")
        medium_flags = sum(1 for f in flags if f.severity == "MEDIUM")

        if high_flags >= 2:
            return "FRAUD_DETECTED"
        if high_flags == 1 and medium_flags >= 1:
            return "FRAUD_DETECTED"
        if high_flags == 0 and medium_flags == 0:
            return "LEGITIMATE"
        return "INCONCLUSIVE"

    def _build_summary(
        self,
        reports: list[ModelReport],
        flags: list[RedFlag],
        verdict: str,
    ) -> str:
        """Build a human-readable summary of the analysis.

        Args:
            reports: Per-model reports.
            flags: Detected red flags.
            verdict: Overall verdict.

        Returns:
            Formatted summary string.
        """
        lines = [f"Deep Analysis — Verdict: {verdict}", ""]
        lines.append(f"Models analyzed: {len(reports)}")
        lines.append(f"Red flags detected: {len(flags)}")
        lines.append("")
        for report in reports:
            lines.append(f"• {report.model_name} ({report.provider})")
            lines.append(f"  Probes: {report.total_probes}, Errors: {report.errors}")
            lines.append(f"  Avg latency: {report.avg_latency_ms:.0f}ms")
            if report.identity_claims:
                lines.append(f"  Identity claims: {', '.join(report.identity_claims[:3])}")
            if report.knowledge_cutoffs:
                lines.append(f"  Knowledge cutoffs: {', '.join(set(report.knowledge_cutoffs))}")
        if flags:
            lines.append("")
            lines.append("Red Flags:")
            for flag in flags:
                lines.append(f"  [{flag.severity}] {flag.category}: {flag.description}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _extract_identity_claims(results: list) -> list[str]:
    """Extract model identity claims from response texts.

    Args:
        results: Benchmark results (identity-related responses).

    Returns:
        Deduplicated list of claimed model names.
    """
    claims: set[str] = set()
    for r in results:
        if not r.response_text or r.prompt_category != "identity":
            continue
        matches = _MODEL_NAME_PATTERN.findall(r.response_text)
        claims.update(m.strip().lower() for m in matches)
    return sorted(claims)


def _extract_knowledge_cutoffs(results: list) -> list[str]:
    """Extract knowledge cutoff dates from response texts.

    Args:
        results: Benchmark results.

    Returns:
        List of mentioned cutoff dates.
    """
    cutoffs: list[str] = []
    for r in results:
        if not r.response_text:
            continue
        matches = _CUTOFF_PATTERN.findall(r.response_text)
        cutoffs.extend(m.strip() for m in matches)
    return cutoffs


def _fingerprint_similarity(fp_a: dict, fp_b: dict) -> float:
    """Compute similarity between two fingerprint dicts.

    Compares style, vocabulary, and structure dimensions.

    Args:
        fp_a: First fingerprint dict.
        fp_b: Second fingerprint dict.

    Returns:
        Similarity score 0.0-1.0.
    """
    if "error" in fp_a or "error" in fp_b:
        return 0.5

    candidates: list[float | None] = [
        _compare_numeric(fp_a, fp_b, "style", "avg_word_count"),
        _compare_numeric(fp_a, fp_b, "style", "uses_markdown"),
        _compare_numeric(fp_a, fp_b, "style", "uses_bullet_lists"),
        _compare_numeric(fp_a, fp_b, "vocabulary", "unique_ratio"),
        _compare_numeric(fp_a, fp_b, "vocabulary", "hedging_ratio"),
        _compare_numeric(fp_a, fp_b, "vocabulary", "confidence_ratio"),
        _compare_numeric(fp_a, fp_b, "structure", "avg_paragraph_count"),
        _compare_numeric(fp_a, fp_b, "structure", "starts_with_greeting_ratio"),
    ]
    valid = [s for s in candidates if s is not None]
    return sum(valid) / max(len(valid), 1)


def _compare_numeric(
    fp_a: dict, fp_b: dict, section: str, key: str
) -> float | None:
    """Compare a single numeric metric between two fingerprints.

    Args:
        fp_a: First fingerprint.
        fp_b: Second fingerprint.
        section: Fingerprint section (style, vocabulary, structure).
        key: Metric key within the section.

    Returns:
        Similarity 0.0-1.0, or None if data missing.
    """
    val_a = _safe_get(fp_a, section, key)
    val_b = _safe_get(fp_b, section, key)
    if val_a is None or val_b is None:
        return None
    max_val = max(abs(val_a), abs(val_b), 0.001)
    return 1.0 - abs(val_a - val_b) / max_val


def _safe_get(fp: dict, section: str, key: str) -> float | None:
    """Safely retrieve a numeric value from a nested fingerprint dict.

    Args:
        fp: The fingerprint dictionary.
        section: Top-level key (style, vocabulary, etc.).
        key: Nested key.

    Returns:
        The float value or None.
    """
    sec = fp.get(section, {})
    if not isinstance(sec, dict):
        return None
    val = sec.get(key)
    if isinstance(val, (int, float)):
        return float(val)
    return None


def _find_shared_phrases(a: ModelReport, b: ModelReport) -> list[str]:
    """Find notable shared phrases between two model reports.

    Args:
        a: First model report.
        b: Second model report.

    Returns:
        List of shared phrases found in both models' identity claims.
    """
    claims_a = set(a.identity_claims)
    claims_b = set(b.identity_claims)
    return sorted(claims_a & claims_b)


def _similarity_verdict(score: float) -> str:
    """Determine if two models are the same based on similarity score.

    Args:
        score: Similarity score 0.0-1.0.

    Returns:
        SAME_MODEL, DIFFERENT_MODELS, or INCONCLUSIVE.
    """
    if score >= 0.85:
        return "SAME_MODEL"
    if score <= 0.50:
        return "DIFFERENT_MODELS"
    return "INCONCLUSIVE"


def _names_match(requested: str, claimed: str) -> bool:
    """Check if a claimed model name plausibly matches the requested one.

    Args:
        requested: The model name the user requested (lowercase).
        claimed: The model name the AI claimed to be (lowercase).

    Returns:
        True if names are a reasonable match.
    """
    requested = requested.replace("-", " ").replace("_", " ")
    claimed = claimed.replace("-", " ").replace("_", " ")

    req_parts = set(requested.split())
    claim_parts = set(claimed.split())

    # Check if at least the base name overlaps (e.g., "claude" in both)
    return bool(req_parts & claim_parts)
