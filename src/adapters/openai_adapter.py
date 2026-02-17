"""OpenAI adapter — talks to the official OpenAI API."""

import time

import httpx

from src.adapters.base import CompletionResponse, ModelAdapter


class OpenAIAdapter(ModelAdapter):
    """Adapter for the official OpenAI Chat Completions API."""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_key: str = "",
        api_base_url: str = "",
        timeout: int = 30,
    ) -> None:
        base = api_base_url or self.DEFAULT_BASE_URL
        super().__init__(model_name, api_key, base, timeout)

    def _build_headers(self) -> dict[str, str]:
        """Build OpenAI-style Bearer token headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def complete(self, prompt: str, system_prompt: str = "") -> CompletionResponse:
        """Send a chat completion request to OpenAI.

        Args:
            prompt: The user message.
            system_prompt: Optional system instruction.

        Returns:
            Standardized CompletionResponse.
        """
        messages = _build_messages(prompt, system_prompt)
        payload = {"model": self.model_name, "messages": messages}

        client = await self._get_client()
        start = time.perf_counter()

        try:
            response = await client.post(
                f"{self.api_base_url}/chat/completions",
                json=payload,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            response.raise_for_status()
            data = response.json()
            return _parse_openai_response(data, latency_ms)
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


def _build_messages(prompt: str, system_prompt: str) -> list[dict[str, str]]:
    """Build the messages array for OpenAI chat completions."""
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return messages


def _parse_openai_response(data: dict, latency_ms: float) -> CompletionResponse:
    """Parse an OpenAI-format chat completion response."""
    usage = data.get("usage", {})
    choices = data.get("choices", [])
    text = choices[0]["message"]["content"] if choices else ""

    return CompletionResponse(
        text=text,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
        latency_ms=latency_ms,
        raw_response=data,
    )
