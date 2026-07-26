"""Tests for the installed command-line entry point."""

from src.cli import main


def test_cli_help_is_available(capsys) -> None:
    assert main([]) == 0
    assert "Run the LLM Verify API service" in capsys.readouterr().out
