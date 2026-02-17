"""Tests for the generic (OpenAI-compatible) adapter."""

import pytest

from src.adapters.generic_adapter import GenericAdapter


def test_generic_adapter_requires_base_url():
    """GenericAdapter should raise ValueError if no base URL is provided."""
    with pytest.raises(ValueError, match="api_base_url is required"):
        GenericAdapter(model_name="test-model", api_key="key", api_base_url="")


def test_generic_adapter_accepts_valid_base_url():
    """GenericAdapter should initialize successfully with a valid base URL."""
    adapter = GenericAdapter(
        model_name="test-model",
        api_key="test-key",
        api_base_url="https://api.example.com/v1",
    )
    assert adapter.model_name == "test-model"
    assert adapter.api_base_url == "https://api.example.com/v1"


def test_generic_adapter_strips_trailing_slash():
    """GenericAdapter should strip trailing slashes from base URL."""
    adapter = GenericAdapter(
        model_name="test",
        api_key="key",
        api_base_url="https://api.example.com/v1/",
    )
    assert adapter.api_base_url == "https://api.example.com/v1"
