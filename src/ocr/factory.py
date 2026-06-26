from __future__ import annotations

"""Factory for creating extractor instances by provider name."""

from src.ocr.base import BaseExtractor


def create_extractor(provider: str, **kwargs) -> BaseExtractor:
    """Create an extractor for the given provider.

    Args:
        provider: "claude" or "local"
        **kwargs: Passed to the provider constructor.
                  For "claude": api_key (str, optional — falls back to ANTHROPIC_API_KEY env var)

    Raises:
        ValueError: If provider is not recognized.
    """
    if provider == "claude":
        from src.ocr.claude_extractor import ClaudeExtractor
        return ClaudeExtractor(**kwargs)
    if provider == "local":
        from src.ocr.local_extractor import LocalVLMExtractor
        return LocalVLMExtractor(**kwargs)
    raise ValueError(f"unknown provider '{provider}' — choose 'claude' or 'local'")
