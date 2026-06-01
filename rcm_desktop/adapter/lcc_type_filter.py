"""LCC taaktype-laagfilters (slice 28)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import PMTask, TaskType

from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket
from rcm_desktop.adapter.pm_task_policy import is_pm_wettelijk

PM_LAYER_TYPES: tuple[str, ...] = ("REV", "IN", "TST", "SVO", "WET")


@dataclass(frozen=True)
class LCCTypeFilterSet:
    """Multi-select toggles: CM = correctief segment; overige = PM-types."""

    cm: bool = True
    rev: bool = True
    in_task: bool = True
    tst: bool = True
    svo: bool = True
    wet: bool = True

    @classmethod
    def all_on(cls) -> LCCTypeFilterSet:
        return cls()

    def all_pm_on(self) -> bool:
        return self.rev and self.in_task and self.tst and self.svo and self.wet

    def task_matches(self, task: PMTask) -> bool:
        if self.wet and is_pm_wettelijk(task):
            return True
        if self.rev and task.taak_type == TaskType.REV:
            return True
        if self.in_task and task.taak_type == TaskType.IN:
            return True
        if self.tst and task.taak_type == TaskType.TST:
            return True
        if self.svo and task.taak_type == TaskType.SVO:
            return True
        return False

    def apply_to_bucket(
        self,
        bucket: LCCYearBucket,
        *,
        unfiltered_preventief_eur: float,
        filtered_preventief_eur: float,
    ) -> LCCYearBucket:
        correctief = bucket.correctief_eur if self.cm else 0.0
        if not self.all_pm_on() and not any(
            (self.rev, self.in_task, self.tst, self.svo, self.wet)
        ):
            preventief = 0.0
        elif self.all_pm_on():
            preventief = unfiltered_preventief_eur
        else:
            preventief = filtered_preventief_eur
        return LCCYearBucket(
            calendar_year=bucket.calendar_year,
            correctief_eur=correctief,
            preventief_eur=preventief,
        )

    def apply_curve(
        self,
        buckets: tuple[LCCYearBucket, ...],
        *,
        unfiltered_preventief: tuple[float, ...],
        filtered_preventief: tuple[float, ...],
    ) -> tuple[LCCYearBucket, ...]:
        if not (len(buckets) == len(unfiltered_preventief) == len(filtered_preventief)):
            raise ValueError("bucket/reeksen moeten even lang zijn")
        return tuple(
            self.apply_to_bucket(
                b,
                unfiltered_preventief_eur=raw,
                filtered_preventief_eur=filt,
            )
            for b, raw, filt in zip(
                buckets, unfiltered_preventief, filtered_preventief, strict=True
            )
        )
