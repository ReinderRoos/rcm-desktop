"""Tests voor engine.py — analytische rekenkern."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.config import RCMConfig
from rcm_core.engine import (
    compute_detection_delay_hr,
    compute_fm_result,
    compute_pbs_result,
    compute_pm_totals,
    rank_pbs_results,
    run_analytical,
)
from rcm_core.models import (
    FailureType, Faalwijze, PBSItem, PBSResult, PMTask, RCMProject, TaskGroup, TaskType
)
from rcm_core.units import TimeDuration, TimeUnit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config():
    return RCMConfig(lifecycle_years=80.0, modeljaar=2026)


@pytest.fixture
def pbs_nieuw():
    """Bouwdeel dat net gebouwd is (bouwjaar = modeljaar → leeftijd=0)."""
    return PBSItem("PBS-001", "Object A", "El 1", "Bouwdeel X", bouwjaar=2026, ontwerpleeftijd_jaar=40.0)


@pytest.fixture
def pbs_oud():
    """Bouwdeel van 20 jaar oud."""
    return PBSItem("PBS-002", "Object A", "El 1", "Bouwdeel Y", bouwjaar=2006, ontwerpleeftijd_jaar=40.0)


@pytest.fixture
def fm_random(pbs_nieuw):
    return Faalwijze(
        fm_id="FM-001", pbs_id=pbs_nieuw.pbs_id, functie_id="FUNC-001",
        faalwijze_omschrijving="Willekeurig falen",
        failure_type=FailureType.RANDOM, mttf_jaar=20.0,
        is_evident=True,
        p_ongewenste_gebeurtenis=1.0,
        downtime_per_failure=TimeDuration(48.0, TimeUnit.HOURS),
        cost_cm_eur=5000.0,
    )


@pytest.fixture
def fm_aging():
    return Faalwijze(
        fm_id="FM-002", pbs_id="PBS-002", functie_id="FUNC-001",
        faalwijze_omschrijving="Verouderingsfalen",
        failure_type=FailureType.AGING, mttf_jaar=50.0,
        is_evident=True,
        downtime_per_failure=TimeDuration(1.0, TimeUnit.DAYS),
        cost_cm_eur=10_000.0,
    )


@pytest.fixture
def fm_hidden(pbs_nieuw):
    """Niet-merkbaar falen — detectie via jaarlijkse inspectie."""
    return Faalwijze(
        fm_id="FM-003", pbs_id=pbs_nieuw.pbs_id, functie_id="FUNC-001",
        faalwijze_omschrijving="Verborgen falen",
        failure_type=FailureType.RANDOM, mttf_jaar=20.0,
        is_evident=False,
        downtime_per_failure=TimeDuration(24.0, TimeUnit.HOURS),
        cost_cm_eur=2000.0,
    )


@pytest.fixture
def pm_svo():
    return PMTask(
        pm_id="PM-001", fm_id="FM-001", taak_type=TaskType.SVO,
        interval_jaar=1.0,
        duration=TimeDuration(4.0, TimeUnit.HOURS),
        cost_eur=200.0,
    )


@pytest.fixture
def pm_inspectie():
    return PMTask(
        pm_id="PM-002", fm_id="FM-003", taak_type=TaskType.IN,
        interval_jaar=1.0,
        duration=TimeDuration(8.0, TimeUnit.HOURS),
        cost_eur=500.0,
    )


# ---------------------------------------------------------------------------
# Tests voor detectievertraging
# ---------------------------------------------------------------------------

class TestDetectionDelay:
    def test_evident_failure_has_no_delay(self, fm_random):
        delay = compute_detection_delay_hr(fm_random, [])
        assert delay == 0.0

    def test_hidden_with_annual_inspection(self, fm_hidden, pm_inspectie):
        """Jaarlijkse inspectie → gemiddelde detectievertraging = 0,5 jaar = 4380 uur."""
        delay = compute_detection_delay_hr(fm_hidden, [pm_inspectie])
        expected = (1.0 * 8760.0) / 2.0
        assert abs(delay - expected) < 1.0

    def test_hidden_no_inspection_returns_inf(self, fm_hidden):
        delay = compute_detection_delay_hr(fm_hidden, [])
        assert delay == float("inf")

    def test_shortest_interval_used(self, fm_hidden):
        pm_1yr = PMTask("PM-A", "FM-003", TaskType.IN, interval_jaar=1.0, duration=TimeDuration(0, TimeUnit.HOURS), cost_eur=0)
        pm_2yr = PMTask("PM-B", "FM-003", TaskType.IN, interval_jaar=2.0, duration=TimeDuration(0, TimeUnit.HOURS), cost_eur=0)
        delay = compute_detection_delay_hr(fm_hidden, [pm_1yr, pm_2yr])
        expected = (1.0 * 8760.0) / 2.0
        assert abs(delay - expected) < 1.0


# ---------------------------------------------------------------------------
# Tests voor PM-kosten en downtime
# ---------------------------------------------------------------------------

class TestPMTotals:
    def test_simple_pm_cost(self, config):
        """SVO jaarlijks, €200/keer, lifecycle=80 → €16.000."""
        pm = PMTask("PM-001", "FM-001", TaskType.SVO, interval_jaar=1.0,
                    duration=TimeDuration(4.0, TimeUnit.HOURS), cost_eur=200.0)
        cost, downtime, _ = compute_pm_totals([pm], {}, config.lifecycle_years)
        assert abs(cost - 16_000.0) < 1e-6
        assert downtime == 0.0

    def test_pm_with_unavailability(self, config):
        """REV elke 10 jaar, 1 dag duur, 100% niet-beschikbaar."""
        pm = PMTask(
            "PM-001", "FM-001", TaskType.REV, interval_jaar=10.0,
            duration=TimeDuration(1.0, TimeUnit.DAYS), cost_eur=5000.0,
            causes_unavailability=True, unavailability_fraction=1.0,
        )
        cost, downtime, _ = compute_pm_totals([pm], {}, config.lifecycle_years)
        assert abs(cost - 40_000.0) < 1e-6         # 8 × €5000
        assert abs(downtime - 8 * 24.0) < 1e-6    # 8 × 24 uur

    def test_task_group_cost_once(self, config):
        """Taakgroep gekoppeld aan twee FM's → kosten maar éénmalig."""
        tg = TaskGroup("TG-001", "Jaarlijkse ronde", TaskType.IN, interval_jaar=1.0,
                       duration=TimeDuration(0, TimeUnit.HOURS), cost_eur=1000.0)
        pm1 = PMTask("PM-001", "FM-001", TaskType.IN, interval_jaar=1.0,
                     duration=TimeDuration(0, TimeUnit.HOURS), cost_eur=0.0, task_group_id="TG-001")
        pm2 = PMTask("PM-002", "FM-002", TaskType.IN, interval_jaar=1.0,
                     duration=TimeDuration(0, TimeUnit.HOURS), cost_eur=0.0, task_group_id="TG-001")

        counted: set[str] = set()
        cost1, _, _ = compute_pm_totals([pm1], {"TG-001": tg}, config.lifecycle_years, counted)
        cost2, _, _ = compute_pm_totals([pm2], {"TG-001": tg}, config.lifecycle_years, counted)

        # Totale groepskosten éénmalig: 80 × €1000 = €80.000
        total = cost1 + cost2
        assert abs(total - 80_000.0) < 1e-6


# ---------------------------------------------------------------------------
# Tests voor FM-berekening
# ---------------------------------------------------------------------------

class TestComputeFMResult:
    def test_random_expected_failures(self, fm_random, pbs_nieuw, config):
        """Random, MTTF=20, lifecycle=80, startleeftijd=0 → 4 falingen."""
        result = compute_fm_result(fm_random, pbs_nieuw, [], {}, config)
        assert abs(result.expected_failures - 4.0) < 1e-5

    def test_random_cm_cost(self, fm_random, pbs_nieuw, config):
        """4 falingen × €5000 = €20.000."""
        result = compute_fm_result(fm_random, pbs_nieuw, [], {}, config)
        assert abs(result.expected_cm_cost_eur - 20_000.0) < 0.01

    def test_multiplicity_scales_failures(self, pbs_nieuw, config):
        """multiplicity=3 → 3× zoveel falingen."""
        pbs = PBSItem("PBS-001", "Obj", "El", "BD", multiplicity=3,
                      bouwjaar=pbs_nieuw.bouwjaar, ontwerpleeftijd_jaar=40.0)
        fm = Faalwijze("FM-001", "PBS-001", "FUNC-001", "Test",
                       failure_type=FailureType.RANDOM, mttf_jaar=20.0)
        result = compute_fm_result(fm, pbs, [], {}, config)
        assert abs(result.expected_failures - 12.0) < 1e-5  # 4 × 3

    def test_hidden_failure_adds_detection_delay(self, fm_hidden, pbs_nieuw, pm_inspectie, config):
        """Niet-merkbaar falen → detectievertraging > 0."""
        result = compute_fm_result(fm_hidden, pbs_nieuw, [pm_inspectie], {}, config)
        assert result.expected_detection_delay_hr > 0.0
        assert result.expected_total_downtime_hr > result.expected_raw_downtime_hr

    def test_evident_failure_no_detection_delay(self, fm_random, pbs_nieuw, config):
        result = compute_fm_result(fm_random, pbs_nieuw, [], {}, config)
        assert result.expected_detection_delay_hr == 0.0

    def test_p_ongewenste_gebeurtenis(self, pbs_nieuw, config):
        fm = Faalwijze("FM-001", "PBS-001", "FUNC-001", "Test",
                       failure_type=FailureType.RANDOM, mttf_jaar=20.0,
                       p_ongewenste_gebeurtenis=0.5)
        result = compute_fm_result(fm, pbs_nieuw, [], {}, config)
        expected_risk = result.expected_failures * 0.5
        assert abs(result.risk_contribution - expected_risk) < 1e-10

    def test_pm_downtime_included(self, fm_random, pbs_nieuw, config):
        pm = PMTask("PM-001", "FM-001", TaskType.REV, interval_jaar=10.0,
                    duration=TimeDuration(1.0, TimeUnit.DAYS), cost_eur=5000.0,
                    causes_unavailability=True, unavailability_fraction=1.0)
        result = compute_fm_result(fm_random, pbs_nieuw, [pm], {}, config)
        assert result.expected_pm_downtime_hr > 0.0


# ---------------------------------------------------------------------------
# Tests voor PBS-aggregatie en classificatie
# ---------------------------------------------------------------------------

class TestComputePBSResult:
    def test_aggregation(self, fm_random, pbs_nieuw, config):
        from rcm_core.engine import compute_fm_result
        fm_result = compute_fm_result(fm_random, pbs_nieuw, [], {}, config)
        pbs_result = compute_pbs_result(pbs_nieuw, [fm_result], config)
        assert pbs_result.pbs_id == "PBS-001"
        assert pbs_result.total_expected_failures > 0
        assert pbs_result.unavailability_pct >= 0.0

    def test_unavailability_pct_calculation(self, config):
        """Test expliciete berekening: 8760 uur downtime in 80 jaar → 1.25%."""
        fm_r = FMResult(
            fm_id="FM-001", pbs_id="PBS-001",
            p_failure_lifecycle=0.5, expected_failures=1.0,
            expected_raw_downtime_hr=8760.0,
            expected_detection_delay_hr=0.0,
            expected_total_downtime_hr=8760.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=0.0, pm_cost_eur=0.0,
            total_cost_eur=0.0, risk_contribution=1.0,
        )
        pbs = PBSItem("PBS-001", "Obj", "El", "BD", bouwjaar=2026)
        result = compute_pbs_result(pbs, [fm_r], config)
        expected_pct = 8760.0 / (80.0 * 8760.0) * 100.0
        assert abs(result.unavailability_pct - expected_pct) < 1e-8


# ---------------------------------------------------------------------------
# Integratietest: volledige project-run
# ---------------------------------------------------------------------------

class TestRunAnalytical:
    def test_simple_project(self, config):
        project = RCMProject(config=config)
        pbs = PBSItem("PBS-001", "Obj", "El", "BD", bouwjaar=2026, ontwerpleeftijd_jaar=40.0)
        fm = Faalwijze("FM-001", "PBS-001", "FUNC-001", "Test",
                       failure_type=FailureType.RANDOM, mttf_jaar=20.0,
                       downtime_per_failure=TimeDuration(48.0, TimeUnit.HOURS),
                       cost_cm_eur=5000.0)
        project.pbs_items["PBS-001"] = pbs
        project.faalwijzes["FM-001"] = fm

        fm_results, pbs_results = run_analytical(project, parallel=False)

        assert "FM-001" in fm_results
        assert "PBS-001" in pbs_results
        assert abs(fm_results["FM-001"].expected_failures - 4.0) < 1e-5
        assert pbs_results["PBS-001"].total_expected_failures == fm_results["FM-001"].expected_failures

    def test_rank_by_cost(self, config):
        project = RCMProject(config=config)
        for i, cost in enumerate([1000.0, 50000.0, 10000.0], 1):
            pbs_id = f"PBS-{i:03d}"
            fm_id = f"FM-{i:03d}"
            project.pbs_items[pbs_id] = PBSItem(pbs_id, "Obj", "El", f"BD{i}", bouwjaar=2026)
            project.faalwijzes[fm_id] = Faalwijze(
                fm_id, pbs_id, "FUNC-001", "Test",
                failure_type=FailureType.RANDOM, mttf_jaar=20.0,
                cost_cm_eur=cost,
            )

        fm_results, pbs_results = run_analytical(project, parallel=False)
        ranked = rank_pbs_results(pbs_results)
        costs = [r.total_cost_eur for r in ranked]
        assert costs == sorted(costs, reverse=True)


# Need to import FMResult for the test above
from rcm_core.models import FMResult
