from __future__ import annotations

import pytest

from rcm_desktop.adapter.cm_cost_split_mapper import merge_cm_cost, split_cm_cost


def test_split_and_merge_round_trip_preserves_total() -> None:
    split = split_cm_cost(12_500.0)
    assert merge_cm_cost(split) == pytest.approx(12_500.0)


def test_split_uses_hint_ratio_when_present() -> None:
    split = split_cm_cost(100.0, hint="materiaal=30;arbeid=70")
    assert split.materiaal_eur == pytest.approx(30.0)
    assert split.arbeid_eur == pytest.approx(70.0)
