from __future__ import annotations

"""
Configuration loader — reads YAML configs and provides typed access.
"""

import yaml
from pathlib import Path
from typing import Any


def load_config(config_path: str | Path = "configs/pipeline.yaml") -> dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Configuration dictionary.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_detection_config(config: dict) -> dict:
    """Extract detection-specific config."""
    return config.get("detection", {})


def get_preprocessing_config(config: dict) -> dict:
    """Extract preprocessing-specific config."""
    return config.get("preprocessing", {})


def get_ocr_config(config: dict) -> dict:
    """Extract OCR-specific config."""
    return config.get("ocr", {})
