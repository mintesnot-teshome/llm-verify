"""Repository for BenchmarkRun CRUD operations."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.benchmark import BenchmarkRun


class BenchmarkRepository:
    """Database access layer for benchmark runs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, description: str, prompt_suite: str) -> BenchmarkRun:
        """Create a new benchmark run.

        Args:
            name: Human-readable name for the run.
            description: Optional description.
            prompt_suite: Which prompt suite to use.

        Returns:
            The created BenchmarkRun with generated ID.
        """
        run = BenchmarkRun(
            name=name,
            description=description,
            prompt_suite=prompt_suite,
            status="pending",
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_by_id(self, run_id: str) -> BenchmarkRun | None:
        """Fetch a benchmark run by ID, including its results.

        Args:
            run_id: The UUID of the benchmark run.

        Returns:
            The BenchmarkRun or None if not found.
        """
        stmt = (
            select(BenchmarkRun)
            .where(BenchmarkRun.id == run_id)
            .options(selectinload(BenchmarkRun.results))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[BenchmarkRun]:
        """List benchmark runs ordered by creation date (newest first).

        Args:
            limit: Maximum number of runs to return.
            offset: Number of runs to skip.

        Returns:
            List of BenchmarkRun objects.
        """
        stmt = (
            select(BenchmarkRun)
            .order_by(BenchmarkRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        run_id: str,
        status: str,
        completed_at: datetime | None = None,
    ) -> BenchmarkRun | None:
        """Update the status of a benchmark run.

        Args:
            run_id: The UUID of the benchmark run.
            status: New status (pending, running, completed, failed).
            completed_at: Timestamp when the run completed.

        Returns:
            The updated BenchmarkRun or None if not found.
        """
        run = await self.get_by_id(run_id)
        if run is None:
            return None
        run.status = status
        if completed_at:
            run.completed_at = completed_at
        await self._session.flush()
        return run
