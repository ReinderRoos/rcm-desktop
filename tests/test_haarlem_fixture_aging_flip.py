"""Slice 42 issue 02 — Haarlem fixture aging-heavy contract."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from rcm_core.models import RCMProject

HAARLEM = Path(__file__).resolve().parent / "fixtures" / "awzi_haarlem_waarderpolder_demo.rcm.json"


@pytest.fixture(scope="module")
def haarlem_raw() -> dict:
    return json.loads(HAARLEM.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def haarlem_project(haarlem_raw: dict) -> RCMProject:
    return RCMProject.from_dict(haarlem_raw)


def test_haarlem_has_121_aging_and_no_random_fms(haarlem_project: RCMProject) -> None:
    types = [fm.failure_type.value for fm in haarlem_project.faalwijzes.values()]
    assert types.count("aging") == 121
    assert types.count("random") == 0


def test_haarlem_flipped_fms_have_explicit_sigma_and_aging_metadata(haarlem_raw: dict) -> None:
    """Slice-42 normal-aging + slice-51 Weibull-subset hebben traceerbare aging-metadata."""
    slice42 = [
        fm
        for fm in haarlem_raw["faalwijzes"].values()
        if "slice 42" in (fm.get("aanname_faalmodel") or "").lower()
    ]
    slice51 = [
        fm
        for fm in haarlem_raw["faalwijzes"].values()
        if "slice 51" in (fm.get("aanname_faalmodel") or "").lower()
    ]
    assert len(slice42) + len(slice51) == 58
    assert 15 <= len(slice51) <= 25
    for fm in slice42:
        mttf = float(fm["mttf_jaar"])
        assert fm["failure_type"] == "aging"
        sigma = float(fm["sigma_jaar"])
        assert math.isfinite(sigma)
        assert sigma > 0.0
        assert sigma < mttf
        assert "normaalverdeling" in fm["aanname_faalmodel"].lower()
        assert fm.get("notes")
    for fm in slice51:
        assert fm["failure_type"] == "aging"
        assert fm.get("aging_distribution") == "weibull_2p"
        assert float(fm.get("beta_jaar", 0)) > 0.0
        assert fm.get("library_ref")
