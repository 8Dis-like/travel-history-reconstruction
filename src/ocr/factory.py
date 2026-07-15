from __future__ import annotations

"""Factory for creating extractor instances by provider name or from config."""

from pathlib import Path
from typing import Any

from src.ocr.base import BaseExtractor


def create_extractor(provider: str, **kwargs) -> BaseExtractor:
    """Create an extractor for the given provider.

    Args:
        provider: "claude" or "local"
        **kwargs: Passed to the provider constructor.
                  For "claude": model (str), max_tokens (int), api_key (str,
                  optional — falls back to ANTHROPIC_API_KEY env var)

    Raises:
        ValueError: If provider is not recognized.
    """
    if provider == "claude":
        from src.ocr.claude_extractor import ClaudeExtractor
        return ClaudeExtractor(**kwargs)
    if provider == "local":
        from src.ocr.local_extractor import LocalVLMExtractor
        return LocalVLMExtractor(**kwargs)
    if provider == "deepseek":
        from src.ocr.deepseek_extractor import DeepseekExtractor
        return DeepseekExtractor(**kwargs)
    if provider == "gemini":
        from src.ocr.gemini_extractor import GeminiExtractor
        return GeminiExtractor(**kwargs)
    raise ValueError(f"unknown provider '{provider}' — choose 'claude', 'local', 'deepseek', or 'gemini'")


def create_extractor_from_config(
    config: dict[str, Any] | None = None,
    config_path: str | Path = "configs/pipeline.yaml",
) -> BaseExtractor:
    """Create an extractor from the pipeline YAML config's `ocr` section.

    The `ocr.engine` value selects the provider, and the matching `ocr.<engine>`
    sub-block supplies its constructor kwargs (e.g. model, max_tokens). This is
    the config-driven entry point the pipeline uses; nothing about which model
    runs is hardcoded in the extractor.

    Args:
        config: Already-loaded config dict. If None, loaded from `config_path`.
        config_path: Path to the pipeline YAML (used only when `config` is None).
    """
    from src.utils.config import get_ocr_config, load_config

    if config is None:
        config = load_config(config_path)

    ocr = get_ocr_config(config)
    engine = ocr.get("engine", "claude")
    params = ocr.get(engine) or {}
    return create_extractor(engine, **params)
