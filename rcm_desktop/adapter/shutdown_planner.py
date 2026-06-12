"""Qt-vrije afsluit-planner voor de resultatenwerkruimte (slice 78)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ShutdownStep(str, Enum):
    RESOLVE_GRID_DIRTY = "resolve_grid_dirty"
    CONFIRM_BUSY_CANCEL = "confirm_busy_cancel"
    CLOSE = "close"


@dataclass(frozen=True)
class ShutdownPlan:
    steps: tuple[ShutdownStep, ...]


def plan_shutdown(*, grid_dirty: bool, busy: bool) -> ShutdownPlan:
    steps: list[ShutdownStep] = []
    if grid_dirty:
        steps.append(ShutdownStep.RESOLVE_GRID_DIRTY)
    if busy:
        steps.append(ShutdownStep.CONFIRM_BUSY_CANCEL)
    steps.append(ShutdownStep.CLOSE)
    return ShutdownPlan(steps=tuple(steps))
