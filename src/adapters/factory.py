"""Factory for creating model adapters from configuration."""

from src.adapters.anthropic_adapter import AnthropicAdapter
from src.adapters.base import ModelAdapter
from src.adapters.generic_adapter import GenericAdapter
from src.adapters.openai_adapter import OpenAIAdapter
from src.config import get_settings
from src.schemas.result import ModelConfig

_ADAPTER_MAP: dict[str, type[ModelAdapter]] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "generic": GenericAdapter,
}

# Default protocol for each provider (used when ModelConfig.protocol is empty)
_DEFAULT_PROTOCOL: dict[str, str] = {
    "openai": "openai",
    "anthropic": "anthropic",
    "suspect": "anthropic",
    "generic": "openai",
}


def create_adapter(config: ModelConfig, timeout: int | None = None) -> ModelAdapter:
    """Create a model adapter from a ModelConfig schema.

    Args:
        config: The model configuration with provider, name, key, and URL.
        timeout: Override the default timeout (seconds).

    Returns:
        An initialized ModelAdapter ready to use.

    Raises:
        ValueError: If the provider is not recognized.
    """
    protocol = config.protocol or _DEFAULT_PROTOCOL.get(config.provider, "openai")
    adapter_cls = _ADAPTER_MAP.get(protocol)
    if adapter_cls is None:
        msg = f"Unknown protocol: {protocol!r}. Choose from: {list(_ADAPTER_MAP.keys())}"
        raise ValueError(msg)

    settings = get_settings()
    api_key = _resolve_api_key(config, settings)
    api_base_url = _resolve_base_url(config, settings)
    effective_timeout = timeout or settings.benchmark_timeout

    return adapter_cls(
        model_name=config.model_name,
        api_key=api_key,
        api_base_url=api_base_url,
        timeout=effective_timeout,
    )


def _resolve_api_key(config: ModelConfig, settings: object) -> str:
    """Resolve the API key from config or fall back to environment settings."""
    if config.api_key:
        return config.api_key

    key_map: dict[str, str] = {
        "openai": getattr(settings, "openai_api_key", ""),
        "anthropic": getattr(settings, "anthropic_api_key", ""),
        "suspect": getattr(settings, "suspect_api_key", ""),
        "generic": "",
    }
    return key_map.get(config.provider, "")


def _resolve_base_url(config: ModelConfig, settings: object) -> str:
    """Resolve the base URL from config or fall back to environment settings."""
    if config.api_base_url:
        return config.api_base_url

    if config.provider == "suspect":
        return getattr(settings, "suspect_api_base_url", "")
    return ""
