"""Slice 66 — REV-segment conditionele survival (Gaarkeuken-anker)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.distributions import _conditional_failures_with_rev_segments

# Gaarkeuken FM 06H-350.2.12.2.1.A.1 — aging normaal, oud asset + REV elke 20 jr
_ANCHOR_AGE = 44.0
_ANCHOR_MTTF = 25.0
_ANCHOR_SIGMA = 3.75
_ANCHOR_REV: tuple[tuple[float, float], ...] = ((20.0, 1.0),)


def test_old_asset_with_two_rev_cycles_does_not_explode_expected_failures() -> None:
    """Studie over twee REV-cycli mag geen ×450k faalmomenten geven."""
    rem_clock = 90.0 - _ANCHOR_AGE  # lifecycle-eind 90 → 46 jr studieduur

    failures = _conditional_failures_with_rev_segments(
        _ANCHOR_AGE,
        clock_start=0.0,
        rem_clock=rem_clock,
        mttf=_ANCHOR_MTTF,
        sigma=_ANCHOR_SIGMA,
        rev_schedule=_ANCHOR_REV,
    )

    assert failures < 50.0


def test_old_asset_with_one_rev_cycle_has_plausible_expected_failures() -> None:
    """Eén REV-cyclus in het venster — orde van grootte ~1–3, niet honderdduizenden."""
    rem_clock = 70.0 - _ANCHOR_AGE  # lifecycle-eind 70 → 26 jr studieduur

    failures = _conditional_failures_with_rev_segments(
        _ANCHOR_AGE,
        clock_start=0.0,
        rem_clock=rem_clock,
        mttf=_ANCHOR_MTTF,
        sigma=_ANCHOR_SIGMA,
        rev_schedule=_ANCHOR_REV,
    )

    assert 0.5 < failures < 5.0


def test_two_rev_cycles_truncated_normal_does_not_explode() -> None:
    rem_clock = 90.0 - _ANCHOR_AGE
    failures = _conditional_failures_with_rev_segments(
        _ANCHOR_AGE,
        clock_start=0.0,
        rem_clock=rem_clock,
        mttf=_ANCHOR_MTTF,
        sigma=_ANCHOR_SIGMA,
        aging_distribution="truncated_normal_0",
        rev_schedule=_ANCHOR_REV,
    )
    assert failures < 50.0


def test_two_rev_cycles_weibull_does_not_explode() -> None:
    rem_clock = 90.0 - _ANCHOR_AGE
    failures = _conditional_failures_with_rev_segments(
        _ANCHOR_AGE,
        clock_start=0.0,
        rem_clock=rem_clock,
        mttf=_ANCHOR_MTTF,
        sigma=_ANCHOR_SIGMA,
        aging_distribution="weibull_2p",
        beta_jaar=3.0,
        rev_schedule=_ANCHOR_REV,
    )
    assert failures < 50.0
