"""Generic adapter for OpenAI-compatible APIs (suspect endpoints, local models, etc.)."""

from src.adapters.openai_adapter import OpenAIAdapter


class GenericAdapter(OpenAIAdapter):
    """Adapter for any endpoint that speaks the OpenAI Chat Completions protocol.

    This is the primary adapter for testing suspect APIs — just point it at
    the suspect's base URL and it will use the standard OpenAI format.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str = "",
        api_base_url: str = "",
        timeout: int = 30,
    ) -> None:
        if not api_base_url:
            msg = "api_base_url is required for GenericAdapter"
            raise ValueError(msg)
        super().__init__(model_name, api_key, api_base_url, timeout)
