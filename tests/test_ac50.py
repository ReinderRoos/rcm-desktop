"""Slice 27 issue 01 — AC-50 eerste-faling en fixture mttf20_sigma3."""
from __future__ import annotations

import pytest

from rcm_core.distributions import (
    ac50_mass_fraction_strictly_after_mttf,
    first_failure_mass_per_calendar_bucket,
)


@pytest.mark.parametrize(
    "mttf,sigma,lifecycle",
    [
        (10.0, 1.5, 60.0),
        (20.0, 3.0, 80.0),
        (30.0, 4.5, 90.0),
    ],
)
def test_ac50_first_failure_mass_after_mttf(mttf: float, sigma: float, lifecycle: float) -> None:
    masses = first_failure_mass_per_calendar_bucket(
        current_age=0.0,
        lifecycle_years=lifecycle,
        mttf=mttf,
        sigma=sigma,
    )
    frac = ac50_mass_fraction_strictly_after_mttf(masses, mttf_jaar=mttf)
    assert 0.495 <= frac <= 0.505, f"mttf={mttf} frac={frac:.4f}"


def test_ac50_mttf_overlap_bucket_is_phi_split_not_point_mass() -> None:
    """Massa op het MTTF-kalenderjaar is geen volledige bucket — AC-50 blijft binnen band."""
    mttf = 20.0
    masses = first_failure_mass_per_calendar_bucket(
        current_age=0.0,
        lifecycle_years=80.0,
        mttf=mttf,
        sigma=3.0,
    )
    idx = int(mttf) - 1
    assert masses[idx] < sum(masses) * 0.15
    frac = ac50_mass_fraction_strictly_after_mttf(masses, mttf_jaar=mttf)
    assert 0.495 <= frac <= 0.505


def test_mttf20_sigma3_screenshot_shape() -> None:
    """Optionele demo-fixture: MTTF=20, σ=3, startleeftijd 0."""
    masses = first_failure_mass_per_calendar_bucket(
        current_age=0.0,
        lifecycle_years=80.0,
        mttf=20.0,
        sigma=3.0,
    )
    total = float(sum(masses))
    assert total > 0.0
    year18 = masses[17] / total
    assert 0.092 <= year18 <= 0.105
    peak = max(masses[18:21]) / total
    assert 0.12 <= peak <= 0.14
    peak_idx = 18 + masses[18:21].index(max(masses[18:21]))
    assert peak_idx in (18, 19, 20)
