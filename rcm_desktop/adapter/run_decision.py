"""Run-beslissingsmodule: incrementele cache vs volledige herberekening (slice 36)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RunUserIntent(Enum):
    """Gebruikersintentie bij Start/Herbereken analyse."""

    START_ANALYSE = "start_analyse"
    FORCE_RECOMPUTE = "force_recompute"


@dataclass(frozen=True)
class RunExecutionOptions:
    full_recompute: bool
    parallel: bool


def resolve_run_execution(*, user_intent: RunUserIntent) -> RunExecutionOptions:
    """Bepaal motor-parameters uit gebruikersintentie.

    Parallel blijft uit tot taakgroep-PM-kosten in ``compute_all_fm_results`` correct
    worden gededupliceerd (parallel workers delen geen ``counted_group_ids``).
    """
    if user_intent == RunUserIntent.FORCE_RECOMPUTE:
        return RunExecutionOptions(full_recompute=True, parallel=False)
    return RunExecutionOptions(full_recompute=False, parallel=False)
