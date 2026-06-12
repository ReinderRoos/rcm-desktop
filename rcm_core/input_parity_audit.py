"""Invoerparity-audit t.o.v. AW-import metadata (slice 67, Qt-vrij)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.fm_parity_diagnostics import compute_fm_input_diagnostics
from rcm_core.models import RCMProject


@dataclass(frozen=True)
class InputParityMismatch:
    fm_id: str
    dimension: str
    rcm_value: float
    aw_value: float


@dataclass(frozen=True)
class InputParityAudit:
    mismatches: tuple[InputParityMismatch, ...]
    fm_count: int

    def count_by_dimension(self, dimension: str) -> int:
        return sum(1 for m in self.mismatches if m.dimension == dimension)


def audit_input_parity(
    project: RCMProject,
    *,
    age_tolerance_years: float = 0.05,
    mttf_tolerance_years: float = 0.001,
) -> InputParityAudit:
    """Vergelijk RCM2-invoer met isograph_causes (InitialAge, FmMttf)."""
    mismatches: list[InputParityMismatch] = []
    for fm_id in sorted(project.faalwijzes):
        diag = compute_fm_input_diagnostics(project, fm_id)
        if (
            diag.initial_age_aw_years is not None
            and abs(diag.current_age_years - diag.initial_age_aw_years)
            > age_tolerance_years
        ):
            mismatches.append(
                InputParityMismatch(
                    fm_id=fm_id,
                    dimension="initial_age",
                    rcm_value=diag.current_age_years,
                    aw_value=diag.initial_age_aw_years,
                )
            )
        if (
            diag.mttf_aw_years is not None
            and abs(diag.mttf_years - diag.mttf_aw_years) > mttf_tolerance_years
        ):
            mismatches.append(
                InputParityMismatch(
                    fm_id=fm_id,
                    dimension="mttf",
                    rcm_value=diag.mttf_years,
                    aw_value=diag.mttf_aw_years,
                )
            )
    return InputParityAudit(
        mismatches=tuple(mismatches),
        fm_count=len(project.faalwijzes),
    )
