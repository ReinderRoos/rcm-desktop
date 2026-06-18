"""Diagnostic: MC P50 vs analytical LCC on Haarlem demo."""
from __future__ import annotations

from pathlib import Path

from rcm_core.cm_overlay import materialize_cm_overlay_project
from rcm_core.engine import compute_all_fm_results
from rcm_core.lcc_profile import build_cm_eur_per_bucket, build_cor_eur_per_bucket
from rcm_core.persistence import load_project

from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve
from rcm_desktop.adapter.run_service import build_run_result, _resolve_run_project
from rcm_desktop.adapter.simulation_engine_service import (
    build_run_result_from_mc_p50,
    run_monte_carlo,
)


def main() -> None:
    fixture = Path("tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json")
    project = load_project(fixture)
    cfg = project.config
    print(
        f"config lifecycle={cfg.lifecycle_years} aw_mc={cfg.aw_mc_lifecycle_horizon} "
        f"modeljaar={cfg.modeljaar} n_fms={len(project.faalwijzes)}"
    )

    raw = project
    overlay = _resolve_run_project(project, None)
    print(f"overlay changed pm count: {len(raw.pm_tasks)} -> {len(overlay.pm_tasks)}")

    fm_overlay = list(compute_all_fm_results(overlay).values())
    anal_run = build_run_result(overlay, fm_overlay)

    mc_raw = run_monte_carlo(raw, n=200, seed=42)
    mc_overlay = run_monte_carlo(overlay, n=200, seed=42)
    print(f"mc raw status={mc_raw.status} mc overlay status={mc_overlay.status}")
    mc_run_raw = build_run_result_from_mc_p50(raw, mc_raw)
    mc_run_overlay = build_run_result_from_mc_p50(overlay, mc_overlay)

    for label, run in [
        ("Analytical (overlay)", anal_run),
        ("MC P50 (raw project)", mc_run_raw),
        ("MC P50 (overlay project)", mc_run_overlay),
    ]:
        curve = build_lcc_planning_curve(raw, run)
        if curve is None:
            continue
        buckets = curve.display_buckets
        totals = [b.correctief_eur + b.preventief_eur for b in buckets]
        cm = [b.correctief_eur for b in buckets]
        pm = [b.preventief_eur for b in buckets]
        nz = [t for t in totals if t > 0]
        print(f"--- LCC display {label} ---")
        print(
            f"  cm_mean={sum(cm)/len(cm):.1f} pm_mean={sum(pm)/len(pm):.1f} "
            f"total_mean={sum(totals)/len(totals):.1f}"
        )
        print(f"  cm_total={sum(cm):.1f} pm_total={sum(pm):.1f}")
        if nz:
            print(f"  flat_total={min(nz):.1f}-{max(nz):.1f}")

    anal_cm = build_cm_eur_per_bucket(raw, anal_run.fm_core_results)
    mc_cm = build_cm_eur_per_bucket(raw, mc_run_raw.fm_core_results)

    def stats(label: str, cm: list[float], run) -> None:
        n = len(cm)
        total = sum(cm)
        exp_cm = sum(r.expected_cm_cost_eur for r in run.fm_core_results)
        exp_fail = sum(r.expected_failures for r in run.fm_core_results)
        print(f"--- {label} ---")
        print(
            f"  buckets={n} total_cm={total:.1f} expected_cm={exp_cm:.1f} "
            f"failures={exp_fail:.2f}"
        )
        print(f"  mean_per_year={total / n:.2f} min={min(cm):.2f} max={max(cm):.2f}")

    stats("Analytical", anal_cm, anal_run)
    stats("MC P50 raw", mc_cm, mc_run_raw)
    mc_cm_ov = build_cm_eur_per_bucket(overlay, mc_run_overlay.fm_core_results)
    stats("MC P50 overlay", mc_cm_ov, mc_run_overlay)
    anal_mean = sum(anal_cm) / len(anal_cm)
    mc_mean = sum(mc_cm) / len(mc_cm)
    print(f"Ratio mean MC raw/Analytical: {mc_mean / anal_mean:.2f}x")
    mc_ov_mean = sum(mc_cm_ov) / len(mc_cm_ov)
    print(f"Ratio mean MC overlay/Analytical: {mc_ov_mean / anal_mean:.2f}x")
    print(
        f"Ratio total_cm MC/Analytical: {sum(mc_cm) / sum(anal_cm):.2f}x"
    )
    print(
        f"Ratio failures MC/Analytical: "
        f"{mc_run_raw.metrics.total_lifecycle_faalmomenten / anal_run.metrics.total_lifecycle_faalmomenten:.2f}x"
    )

    # Top 5 FMs by analytical CM cost
    ranked = sorted(
        anal_run.fm_core_results,
        key=lambda r: r.expected_cm_cost_eur,
        reverse=True,
    )[:5]
    print("\nTop 5 FMs by analytical CM:")
    for a in ranked:
        m = next(r for r in mc_run_raw.fm_core_results if r.fm_id == a.fm_id)
        mc_fm = mc_raw.fm_results[a.fm_id]
        ratio = mc_fm.failures.p50 / a.expected_failures if a.expected_failures else 0
        print(
            f"  {a.fm_id}: anal_fail={a.expected_failures:.3f} mc_p50={mc_fm.failures.p50:.3f} "
            f"ratio={ratio:.2f} anal_cm={a.expected_cm_cost_eur:.0f} mc_cm={m.expected_cm_cost_eur:.0f}"
        )


if __name__ == "__main__":
    main()
