"""Runtime feature flags for incremental rollouts."""

from __future__ import annotations

import os


def _enabled_from_env(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def meekoppel_workflow_v2_enabled() -> bool:
    """Toggle for slice54 meekoppel workflow seam."""
    return _enabled_from_env("RCM_MEEKOPPEL_WORKFLOW_V2", default=False)
