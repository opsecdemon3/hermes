# Hermes Phase 0
"""
Feature flags for Hermes functionality
"""

import os


def env_bool(key: str, default: bool = False) -> bool:  # Hermes Phase 0
    """Parse boolean from environment variable"""
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")


HERMES_ENABLED: bool = env_bool("HERMES_ENABLED", default=True)  # Hermes Phase 0
