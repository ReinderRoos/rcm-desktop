from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from rcm_core.distributions import expected_failures_lifecycle, p_failure_by_age, sample_time_to_failure
from rcm_core.editing.validation import validate_entity_rows
from rcm_core.models import AgingDistribution, FailureType, Faalwijze, RCMProject

HAARLEM = Path(__file__).resolve().parent / "fixtures" / "awzi_haarlem_waarderpolder_demo.rcm.json"


def test_legacy_faalwijze_defaults_to_normal_distribution() -> None:
    fm = Faalwijze.from_dict(
        {
            "fm_id": "FM-1",
            "pbs_id": "PBS-1",
            "functie_id": "FUNC-1",
            "faalwijze_omschrijving": "legacy",
            "failure_type": "aging",
            "mttf_jaar": 40.0,
            "sigma_jaar": 6.0,
        }
    )
    assert fm.aging_distribution == AgingDistribution.NORMAL
    assert fm.beta_jaar == 0.0


def test_weibull_conditioned_probability_matches_closed_form() -> None:
    mttf = 40.0
    beta = 2.5
    start_age = 10.0
    end_age = 20.0
    expected = (
        p_failure_by_age(end_age, "aging", mttf, 0.0, "weibull_2p", beta)
        - p_failure_by_age(start_age, "aging", mttf, 0.0, "weibull_2p", beta)
    ) / (1.0 - p_failure_by_age(start_age, "aging", mttf, 0.0, "weibull_2p", beta))
    got = expected_failures_lifecycle(
        start_age,
        end_age,
        "aging",
        mttf,
        0.0,
        1.0,
        aging_distribution="weibull_2p",
        beta_jaar=beta,
    )
    assert math.isclose(got, expected, rel_tol=0.0, abs_tol=1e-9)


def test_truncated_normal_has_zero_mass_below_zero() -> None:
    assert p_failure_by_age(-1.0, "aging", 30.0, 5.0, "truncated_normal_0", 0.0) == 0.0


def test_weibull_beta_is_blocking_in_edit_validation() -> None:
    rows = [
        {
            "fm_id": "FM-1",
            "pbs_id": "PBS-1",
            "failure_type": "aging",
            "aging_distribution": "weibull_2p",
            "mttf_jaar": 40.0,
            "beta_jaar": 0.0,
        }
    ]
    _, errors = validate_entity_rows("faalwijzes", rows, RCMProject(), {"faalwijzes": rows, "pbs": [{"pbs_id": "PBS-1"}]})
    assert "FM-1" in errors
    assert "beta_jaar" in errors["FM-1"]
    assert errors["FM-1"]["beta_jaar"][0]["code"] == "FM_WEIBULL_BETA_MISSING"


def test_weibull_sampling_returns_non_decreasing_age() -> None:
    rng = np.random.default_rng(42)
    ttf = sample_time_to_failure(
        current_age=12.0,
        failure_type=FailureType.AGING.value,
        mttf=40.0,
        sigma=0.0,
        rng=rng,
        aging_distribution="weibull_2p",
        beta_jaar=2.1,
    )
    assert ttf >= 12.0


@pytest.fixture(scope="module")
def haarlem_project() -> RCMProject:
    return RCMProject.from_dict(json.loads(HAARLEM.read_text(encoding="utf-8")))


def test_haarlem_has_awzi_aging_defaults_in_bibliotheek(haarlem_project: RCMProject) -> None:
    for bib_id in (
        "BIB-AWZI-AGING-POMP",
        "BIB-AWZI-AGING-KLEP",
        "BIB-AWZI-AGING-MECH",
    ):
        item = haarlem_project.bibliotheek[bib_id]
        assert item.categorie in ("faalmodel", "aging_defaults")
        assert "AWZI" in item.bron or "HWP" in item.bron


def test_haarlem_weibull_subset_is_bounded_and_valid(haarlem_project: RCMProject) -> None:
    weibull = [
        fm
        for fm in haarlem_project.faalwijzes.values()
        if fm.aging_distribution == AgingDistribution.WEIBULL_2P
    ]
    assert 15 <= len(weibull) <= 25
    for fm in weibull:
        assert fm.beta_jaar > 0.0
        assert fm.library_ref
        assert fm.library_ref in haarlem_project.bibliotheek
