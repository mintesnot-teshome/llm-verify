"""Abstract base adapter defining the interface all AI provider adapters must implement."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class CompletionResponse:
    """Standardized response from any AI model adapter."""

    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float | None = None
    raw_response: dict | None = None
    error: str | None = None

    @property
    def is_error(self) -> bool:
        """Check if the response contains an error."""
        return self.error is not None


class ModelAdapter(ABC):
    """Abstract base class for AI model adapters.

    Each provider (OpenAI, Anthropic, generic OpenAI-compatible) implements
    this interface so the benchmark runner can treat them uniformly.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str,
        api_base_url: str,
        timeout: int = 30,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the shared HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self._build_headers(),
            )
        return self._client

    @abstractmethod
    def _build_headers(self) -> dict[str, str]:
        """Build authentication headers for this provider."""

    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str = "") -> CompletionResponse:
        """Send a prompt and return a standardized response.

        Args:
            prompt: The user message to send.
            system_prompt: Optional system instruction.

        Returns:
            A CompletionResponse with the model's reply and metadata.
        """

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "ModelAdapter":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
