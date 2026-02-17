"""Anthropic adapter — talks to the Anthropic Messages API."""

import time

import httpx

from src.adapters.base import CompletionResponse, ModelAdapter


class AnthropicAdapter(ModelAdapter):
    """Adapter for the Anthropic Messages API."""

    DEFAULT_BASE_URL = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-20250514",
        api_key: str = "",
        api_base_url: str = "",
        timeout: int = 30,
    ) -> None:
        base = api_base_url or self.DEFAULT_BASE_URL
        super().__init__(model_name, api_key, base, timeout)

    def _build_headers(self) -> dict[str, str]:
        """Build Anthropic-specific headers."""
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json",
        }

    async def complete(self, prompt: str, system_prompt: str = "") -> CompletionResponse:
        """Send a message to the Anthropic API.

        Args:
            prompt: The user message.
            system_prompt: Optional system instruction.

        Returns:
            Standardized CompletionResponse.
        """
        payload = _build_payload(self.model_name, prompt, system_prompt)
        client = await self._get_client()
        start = time.perf_counter()

        try:
            response = await client.post(
                f"{self.api_base_url}/v1/messages",
                json=payload,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            response.raise_for_status()
            data = response.json()
            return _parse_anthropic_response(data, latency_ms)
        except httpx.HTTPStatusError as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            return CompletionResponse(
                text="",
                latency_ms=latency_ms,
                error=f"HTTP {exc.response.status_code}: {exc.response.text}",
            )
        except httpx.RequestError as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            return CompletionResponse(
                text="",
                latency_ms=latency_ms,
                error=f"Request failed: {exc}",
            )


def _build_payload(model: str, prompt: str, system_prompt: str) -> dict:
    """Build the Anthropic Messages API payload."""
    payload: dict = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        payload["system"] = system_prompt
    return payload


def _parse_anthropic_response(data: dict, latency_ms: float) -> CompletionResponse:
    """Parse an Anthropic Messages API response."""
    content_blocks = data.get("content", [])
    text = "".join(
        block.get("text", "") for block in content_blocks if block.get("type") == "text"
    )
    usage = data.get("usage", {})

    return CompletionResponse(
        text=text,
        prompt_tokens=usage.get("input_tokens"),
        completion_tokens=usage.get("output_tokens"),
        total_tokens=None,  # Anthropic doesn't provide total directly
        latency_ms=latency_ms,
        raw_response=data,
    )
