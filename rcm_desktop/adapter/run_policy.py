"""Run policy — centrale run-parameters (adapter deepening)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RunUserIntent(Enum):
    START_ANALYSE = "start_analyse"
    FORCE_RECOMPUTE = "force_recompute"


@dataclass(frozen=True)
class RunExecutionOptions:
    full_recompute: bool
    parallel: bool


@dataclass(frozen=True)
class RunPolicy:
    """Centrale run-parameters voor enkelvoudige en scenario-runs."""

    allow_parallel: bool = False

    def resolve(self, *, user_intent: RunUserIntent) -> RunExecutionOptions:
        if user_intent == RunUserIntent.FORCE_RECOMPUTE:
            return RunExecutionOptions(full_recompute=True, parallel=False)
        return RunExecutionOptions(full_recompute=False, parallel=self.allow_parallel and False)

    def scenario_options(self) -> RunExecutionOptions:
        return RunExecutionOptions(full_recompute=False, parallel=self.allow_parallel)


DEFAULT_RUN_POLICY = RunPolicy(allow_parallel=False)
SCENARIO_RUN_POLICY = RunPolicy(allow_parallel=True)
