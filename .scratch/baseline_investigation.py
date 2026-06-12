"""Temporary diagnostic: baseline cost delta investigation."""
from __future__ import annotations

import json
from pathlib import Path

from rcm_core.distributions import build_rev_schedule, expected_failures_lifecycle
from rcm_core.engine import run_analytical
from rcm_core.models import RCMProject

HAARLEM = Path("tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json")
project = RCMProject.from_dict(json.loads(HAARLEM.read_text(encoding="utf-8")))

fm_results, _ = run_analytical(project, parallel=False)
total_cost = sum(r.total_cost_eur for r in fm_results.values())
total_cm = sum(r.expected_cm_cost_eur for r in fm_results.values())
total_pm = sum(r.pm_cost_eur for r in fm_results.values())
total_dt = sum(r.expected_total_downtime_hr + r.expected_pm_downtime_hr for r in fm_results.values())

print("=== Current run metrics ===")
print(f"total_cost_eur: {total_cost:,.2f}")
print(f"  CM: {total_cm:,.2f}")
print(f"  PM: {total_pm:,.2f}")
print(f"total_downtime_hr: {total_dt:,.1f}")
ly = project.config.lifecycle_years
print(f"unavailability_pct: {(total_dt / (ly * 8760)) * 100:.2f}")
print()
print("=== Baseline expected ===")
print("total_cost_eur: 47,782,827.67")
print("total_downtime_hr: 460,353.0")
print("unavailability_pct: 87.59")
print(f"delta cost: {total_cost - 47_782_827.67:,.2f} ({100*(total_cost/47_782_827.67 - 1):+.1f}%)")

by_type: dict[str, dict[str, float]] = {}
for fm_id, r in fm_results.items():
    ft = project.faalwijzes[fm_id].failure_type.value
    by_type.setdefault(ft, {"cm": 0.0, "pm": 0.0, "total": 0.0, "count": 0.0})
    by_type[ft]["cm"] += r.expected_cm_cost_eur
    by_type[ft]["pm"] += r.pm_cost_eur
    by_type[ft]["total"] += r.total_cost_eur
    by_type[ft]["count"] += 1

print("\n=== Cost by failure type ===")
for ft, d in sorted(by_type.items()):
    print(
        f"{ft:20s} n={int(d['count']):3d}  "
        f"CM={d['cm']:>14,.0f}  PM={d['pm']:>14,.0f}  total={d['total']:>14,.0f}"
    )

aging_fms = [fm for fm in project.faalwijzes.values() if fm.failure_type.value == "aging"]
tot_with = tot_without = 0.0
cm_with = cm_without = 0.0
for fm in aging_fms:
    pbs = project.pbs_items[fm.pbs_id]
    eff_bouwjaar = pbs.effective_bouwjaar(project.pbs_items)
    ca = float(project.config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
    mult = pbs.effective_multiplicity(project.pbs_items)
    pm = project.get_pm_tasks_for_fm(fm.fm_id)
    rev = build_rev_schedule(pm)
    w = (
        expected_failures_lifecycle(
            ca,
            project.config.lifecycle_years,
            "aging",
            fm.mttf_jaar,
            fm.effective_sigma,
            fm.repair_quality,
            rev_schedule=rev,
        )
        * mult
    )
    wo = (
        expected_failures_lifecycle(
            ca,
            project.config.lifecycle_years,
            "aging",
            fm.mttf_jaar,
            fm.effective_sigma,
            fm.repair_quality,
            rev_schedule=(),
        )
        * mult
    )
    tot_with += w
    tot_without += wo
    cm_with += fm.cost_cm_eur * w
    cm_without += fm.cost_cm_eur * wo

print(f"\nAging FMs: {len(aging_fms)}")
print(f"Expected failures with REV: {tot_with:,.1f}")
print(f"Expected failures without REV: {tot_without:,.1f}")
print(f"CM cost with REV: {cm_with:,.0f}")
print(f"CM cost without REV: {cm_without:,.0f}")
print(f"CM delta (no REV - with REV): {cm_without - cm_with:,.0f}")

# Compare engine CM for aging vs manual no-rev
engine_aging_cm = sum(
    r.expected_cm_cost_eur
    for fm_id, r in fm_results.items()
    if project.faalwijzes[fm_id].failure_type.value == "aging"
)
print(f"\nEngine aging CM (with REV): {engine_aging_cm:,.0f}")
print(f"Manual aging CM (no REV):   {cm_without:,.0f}")
print(f"Gap engine vs no-rev manual: {cm_without - engine_aging_cm:,.0f}")

# Top aging FMs by CM delta
rows = []
for fm in aging_fms:
    pbs = project.pbs_items[fm.pbs_id]
    eff_bouwjaar = pbs.effective_bouwjaar(project.pbs_items)
    ca = float(project.config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
    mult = pbs.effective_multiplicity(project.pbs_items)
    pm = project.get_pm_tasks_for_fm(fm.fm_id)
    rev = build_rev_schedule(pm)
    w = expected_failures_lifecycle(
        ca, project.config.lifecycle_years, "aging", fm.mttf_jaar, fm.effective_sigma,
        fm.repair_quality, rev_schedule=rev,
    ) * mult
    wo = expected_failures_lifecycle(
        ca, project.config.lifecycle_years, "aging", fm.mttf_jaar, fm.effective_sigma,
        fm.repair_quality, rev_schedule=(),
    ) * mult
    delta = fm.cost_cm_eur * (wo - w)
    if delta > 1000:
        rows.append((delta, fm.fm_id[:16], len(rev), w, wo, fm.cost_cm_eur))

rows.sort(reverse=True)
print("\n=== Top aging FMs by CM saved due to REV ===")
for delta, fm_id, n_rev, w, wo, cost in rows[:10]:
    print(f"  {fm_id} rev={n_rev} ef_with={w:.2f} ef_no={wo:.2f} cost_cm={cost:,.0f} saved={delta:,.0f}")
