"""Deep analysis API handler — run full fraud detection analysis."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.analysis import DeepAnalysisReport, DeepAnalysisRequest
from src.services.deep_analysis import DeepAnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/deep", response_model=DeepAnalysisReport)
async def run_deep_analysis(
    request: DeepAnalysisRequest,
    session: AsyncSession = Depends(get_session),
) -> DeepAnalysisReport:
    """Run a comprehensive deep analysis against suspect model endpoints.

    Executes all requested prompt suites (identity, capability, fingerprint)
    against every configured model, cross-compares fingerprints, and generates
    a fraud report with red flags and an overall verdict.

    Args:
        request: Analysis configuration with model endpoints and suites.
        session: Database session (injected).

    Returns:
        DeepAnalysisReport with per-model reports, comparisons, red flags, and verdict.
    """
    service = DeepAnalysisService(session)
    return await service.analyze(request)
