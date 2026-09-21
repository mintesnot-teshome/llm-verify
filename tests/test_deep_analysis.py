"""Adversarial tests for fail-closed deep-analysis behavior."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.schemas.analysis import ModelReport, RedFlag
from src.services.deep_analysis import (
    DeepAnalysisService,
    _evidence_quality,
    _extract_identity_claims,
    _extract_proxy_indicators,
    _names_match,
    _similarity_verdict,
)


def _service() -> DeepAnalysisService:
    return DeepAnalysisService(MagicMock())


def _report(**overrides: object) -> ModelReport:
    values: dict[str, object] = {
        "model_name": "claude-sonnet-4-20250514",
        "provider": "suspect",
        "total_probes": 32,
        "successful_probes": 32,
        "evidence_quality": "SUFFICIENT",
    }
    values.update(overrides)
    return ModelReport(**values)


def test_no_flags_is_not_called_legitimate() -> None:
    verdict = _service()._determine_verdict([], [_report()])
    assert verdict == "NO_FRAUD_SIGNALS"


def test_missing_evidence_never_receives_clean_verdict() -> None:
    report = _report(
        total_probes=10,
        successful_probes=0,
        errors=10,
        error_rate=1.0,
        evidence_quality="INSUFFICIENT",
    )
    flags = _service()._detect_red_flags([report], [])
    verdict = _service()._determine_verdict(flags, [report])

    assert any(flag.category == "evidence" for flag in flags)
    assert verdict in {"SUSPICIOUS", "INCONCLUSIVE"}


def test_one_identity_mismatch_is_suspicious() -> None:
    flags = [
        RedFlag(
            severity="HIGH",
            category="identity",
            description="Model family mismatch",
        )
    ]
    assert _service()._determine_verdict(flags, [_report()]) == "SUSPICIOUS"


def test_model_family_and_version_matching_is_strict() -> None:
    assert _names_match("claude-sonnet-4-20250514", "claude-4")
    assert not _names_match("claude-sonnet-4-20250514", "gpt-4o")
    assert not _names_match("Opus 4.6", "claude-3.5-sonnet")
    assert not _names_match("claude-3.5-sonnet", "claude-3.7-sonnet")


def test_identity_extraction_ignores_comparison_mentions() -> None:
    results = [
        SimpleNamespace(
            response_text="I am Claude-4. I am not GPT-4 and should not be confused with it.",
            prompt_category="identity",
        )
    ]
    assert _extract_identity_claims(results) == ["claude-4"]


def test_identity_extraction_supports_named_claude_variants() -> None:
    results = [
        SimpleNamespace(
            response_text="My model name is Claude Sonnet 4.5.",
            prompt_category="identity",
        )
    ]
    assert _extract_identity_claims(results) == ["claude sonnet 4.5"]


def test_proxy_disclosures_are_extracted() -> None:
    results = [
        SimpleNamespace(
            response_text="Requests reach me through a managed proxy relay operated upstream."
        )
    ]
    indicators = _extract_proxy_indicators(results)
    assert indicators
    assert "proxy" in indicators[0]


def test_proxy_denials_are_not_flagged() -> None:
    results = [
        SimpleNamespace(
            response_text="I do not use a proxy or relay; requests go directly to the provider."
        )
    ]
    assert _extract_proxy_indicators(results) == []


def test_evidence_quality_thresholds() -> None:
    assert _evidence_quality(8, 0.80) == "SUFFICIENT"
    assert _evidence_quality(4, 0.60) == "DEGRADED"
    assert _evidence_quality(2, 1.00) == "INSUFFICIENT"


def test_similarity_requires_enough_successful_probes() -> None:
    assert _similarity_verdict(0.99, 3, 3) == "INCONCLUSIVE"
    assert _similarity_verdict(0.91, 8, 8) == "SAME_MODEL"
