"""Tests voor cache.py — hash-gebaseerde incrementele berekening."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.config import RCMConfig
from rcm_core.models import (
    FailureType,
    Faalwijze,
    PBSItem,
    PMTask,
    RCMProject,
    TaskType,
)
from rcm_core.cache import (
    CACHE_INPUTS_VERSION,
    compute_fm_hash,
    compute_global_digest,
    find_affected_fms,
    load_cache,
    load_cache_snapshot,
    merge_results,
    save_cache,
)
from rcm_core.units import TimeDuration, TimeUnit


def _make_project(mttf: float = 20.0, modeljaar: int = 2026) -> RCMProject:
    config = RCMConfig(lifecycle_years=80.0, modeljaar=modeljaar)
    pbs = PBSItem("PBS-001", "Obj", "El", "BD", bouwjaar=2006, ontwerpleeftijd_jaar=40.0)
    fm = Faalwijze(
        "FM-001", "PBS-001", "FUNC-001", "Test",
        failure_type=FailureType.RANDOM, mttf_jaar=mttf,
        downtime_per_failure=TimeDuration(1.0, TimeUnit.DAYS),
    )
    return RCMProject(
        config=config,
        pbs_items={"PBS-001": pbs},
        faalwijzes={"FM-001": fm},
    )


class TestHashStability:
    def test_same_inputs_same_hash(self):
        """Identieke invoer → identieke hash."""
        project = _make_project()
        h1 = compute_fm_hash(project, "FM-001")
        h2 = compute_fm_hash(project, "FM-001")
        assert h1 == h2

    def test_mttf_change_changes_hash(self):
        """Wijziging in MTTF → andere hash."""
        p1 = _make_project(mttf=20.0)
        p2 = _make_project(mttf=25.0)
        h1 = compute_fm_hash(p1, "FM-001")
        h2 = compute_fm_hash(p2, "FM-001")
        assert h1 != h2

    def test_modeljaar_change_changes_hash(self):
        """Wijziging in modeljaar → andere hash (leeftijd verandert)."""
        p2026 = _make_project(modeljaar=2026)
        p2027 = _make_project(modeljaar=2027)
        h1 = compute_fm_hash(p2026, "FM-001")
        h2 = compute_fm_hash(p2027, "FM-001")
        assert h1 != h2

    def test_pm_task_change_changes_hash(self):
        """Toevoegen van PM-taak → andere hash."""
        project = _make_project()
        h_no_pm = compute_fm_hash(project, "FM-001")

        pm = PMTask("PM-001", "FM-001", TaskType.IN,
                    interval_jaar=1.0, duration=TimeDuration(4.0, TimeUnit.HOURS), cost_eur=200.0)
        with_pm = RCMProject(
            config=project.config,
            pbs_items=dict(project.pbs_items),
            faalwijzes=dict(project.faalwijzes),
            pm_tasks={"PM-001": pm},
        )
        h_with_pm = compute_fm_hash(with_pm, "FM-001")
        assert h_no_pm != h_with_pm

    def test_sibling_pbs_change_changes_fm_hash(self):
        """Slice bevat volledige ``pbs_items``: wijziging aan ander PBS-item wijzigt FM-hash (conservatief)."""
        base = _make_project()
        with_sibling = RCMProject(
            config=base.config,
            pbs_items={
                **base.pbs_items,
                "PBS-002": PBSItem(
                    "PBS-002", "Obj2", "El2", "BD2",
                    bouwjaar=2010, ontwerpleeftijd_jaar=30.0,
                ),
            },
            faalwijzes=dict(base.faalwijzes),
        )
        sibling_bouwjaar_changed = RCMProject(
            config=with_sibling.config,
            pbs_items={
                "PBS-001": with_sibling.pbs_items["PBS-001"],
                "PBS-002": PBSItem(
                    "PBS-002", "Obj2", "El2", "BD2",
                    bouwjaar=2011, ontwerpleeftijd_jaar=30.0,
                ),
            },
            faalwijzes=dict(with_sibling.faalwijzes),
        )
        h_stable = compute_fm_hash(with_sibling, "FM-001")
        h_after = compute_fm_hash(sibling_bouwjaar_changed, "FM-001")
        assert h_stable != h_after


class TestFindAffectedFMs:
    def test_no_cache_all_affected(self):
        """Lege cache → alle FM's zijn affected."""
        project = _make_project()
        affected = find_affected_fms(project, {})
        assert "FM-001" in affected

    def test_fresh_hash_not_affected(self):
        """Sla hash op → FM is niet meer affected."""
        project = _make_project()
        current_hash = compute_fm_hash(project, "FM-001")
        affected = find_affected_fms(project, {"FM-001": current_hash})
        assert "FM-001" not in affected

    def test_stale_hash_is_affected(self):
        """Verouderde hash → FM is affected."""
        project = _make_project()
        affected = find_affected_fms(project, {"FM-001": "verouderde_hash_xxxx"})
        assert "FM-001" in affected


class TestCachePersistence:
    def test_save_load_roundtrip(self, tmp_path):
        """Cache opslaan en herladen geeft identieke hashes."""
        from rcm_core.models import FMResult

        project_path = tmp_path / "test.rcm.json"
        hashes = {"FM-001": "abc123", "FM-002": "def456"}
        # Maak een minimale FMResult voor opslag
        fm_result = FMResult(
            fm_id="FM-001", pbs_id="PBS-001",
            p_failure_lifecycle=0.5, expected_failures=2.0,
            expected_raw_downtime_hr=48.0,
            expected_detection_delay_hr=0.0,
            expected_total_downtime_hr=48.0,
            expected_pm_downtime_hr=0.0,
            expected_cm_cost_eur=10_000.0, pm_cost_eur=0.0,
            total_cost_eur=10_000.0, risk_contribution=2.0,
        )
        project = _make_project()
        save_cache(project_path, hashes, {"FM-001": fm_result}, project)
        loaded_hashes, loaded_results = load_cache(project_path)
        assert loaded_hashes == hashes
        assert "FM-001" in loaded_results
        assert loaded_results["FM-001"]["expected_failures"] == 2.0
        snap = load_cache_snapshot(project, project_path)
        assert snap.global_layer_trusted is True
        assert snap.hashes == hashes
        cache_path = project_path.with_suffix("").with_suffix(".rcm.cache.json")
        on_disk = json.loads(cache_path.read_text(encoding="utf-8"))
        assert on_disk.get("global_digest") == compute_global_digest(project)

    def test_missing_cache_returns_empty(self, tmp_path):
        """Ontbrekend cache-bestand geeft lege dicts terug."""
        path = tmp_path / "nonexistent.rcm.json"
        hashes, results = load_cache(path)
        assert hashes == {}
        assert results == {}


class TestMergeResults:
    def test_fresh_overwrites_cached(self):
        """Verse resultaten overschrijven gecachte resultaten voor dezelfde FM-id."""
        from rcm_core.models import FMResult

        def make_result(fm_id: str, failures: float) -> FMResult:
            return FMResult(
                fm_id=fm_id, pbs_id="PBS-001",
                p_failure_lifecycle=0.5, expected_failures=failures,
                expected_raw_downtime_hr=0.0, expected_detection_delay_hr=0.0,
                expected_total_downtime_hr=0.0, expected_pm_downtime_hr=0.0,
                expected_cm_cost_eur=0.0, pm_cost_eur=0.0,
                total_cost_eur=0.0, risk_contribution=failures,
            )

        fresh = {"FM-001": make_result("FM-001", 5.0)}
        cached_raw = {
            "FM-001": make_result("FM-001", 3.0).to_dict(),  # ouder resultaat
            "FM-002": make_result("FM-002", 7.0).to_dict(),  # niet herberekend
        }
        merged = merge_results(fresh, cached_raw, fresh_fm_ids=["FM-001"])
        assert merged["FM-001"].expected_failures == 5.0   # vers
        assert merged["FM-002"].expected_failures == 7.0   # uit cache


class TestLoadCacheSnapshot:
    def test_missing_digest_treats_cache_as_untrusted(self, tmp_path):
        """PoC (b): zonder ``global_digest`` geen vertrouwen in hashes/results."""
        project_path = tmp_path / "p.rcm.json"
        cache_path = project_path.with_suffix("").with_suffix(".rcm.cache.json")
        cache_path.write_text(
            json.dumps({"hashes": {"FM-001": "abc"}, "results": {}}),
            encoding="utf-8",
        )
        project = _make_project()
        snap = load_cache_snapshot(project, project_path)
        assert snap.cache_file_existed is True
        assert snap.global_layer_trusted is False
        assert snap.hashes == {}
        assert snap.raw_results == {}

    def test_wrong_digest_treats_cache_as_untrusted(self, tmp_path):
        project_path = tmp_path / "p.rcm.json"
        cache_path = project_path.with_suffix("").with_suffix(".rcm.cache.json")
        cache_path.write_text(
            json.dumps(
                {
                    "global_digest": "0" * 64,
                    "hashes": {"FM-001": "stored"},
                    "results": {},
                }
            ),
            encoding="utf-8",
        )
        project = _make_project()
        snap = load_cache_snapshot(project, project_path)
        assert snap.global_layer_trusted is False
        assert snap.hashes == {}

    def test_raw_load_cache_ignores_digest(self, tmp_path):
        """``load_cache`` blijft ruwe schijf tonen (tests / tooling)."""
        project_path = tmp_path / "p.rcm.json"
        cache_path = project_path.with_suffix("").with_suffix(".rcm.cache.json")
        cache_path.write_text(
            json.dumps({"hashes": {"FM-001": "x"}, "results": {}}),
            encoding="utf-8",
        )
        h, r = load_cache(project_path)
        assert h.get("FM-001") == "x"


class TestGlobalDigest:
    def test_same_project_twice_same_digest(self):
        """Zelfde project → twee keer dezelfde globale digest."""
        project = _make_project()
        d1 = compute_global_digest(project)
        d2 = compute_global_digest(project)
        assert d1 == d2
        assert len(d1) == 64

    def test_modeljaar_change_changes_global_digest(self):
        """Wijziging in config die in to_dict() zit wijzigt globale digest."""
        p1 = _make_project(modeljaar=2026)
        p2 = _make_project(modeljaar=2027)
        assert compute_global_digest(p1) != compute_global_digest(p2)

    def test_cache_inputs_version_is_set_for_rcm2(self):
        """RCM2 start met CACHE_INPUTS_VERSION>=100 zodat oude RCM1-caches niet vertrouwd worden."""
        assert CACHE_INPUTS_VERSION >= 100
