"""Run-beslissingsmodule — delegeert naar ``run_policy`` (slice 36)."""
from __future__ import annotations

from rcm_desktop.adapter.run_policy import (
    DEFAULT_RUN_POLICY,
    RunExecutionOptions,
    RunUserIntent,
)


def resolve_run_execution(*, user_intent: RunUserIntent) -> RunExecutionOptions:
    return DEFAULT_RUN_POLICY.resolve(user_intent=user_intent)
