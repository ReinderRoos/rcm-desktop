"""
rcm_core.cli — CLI-ingangspunt voor de RCM2 (rcm-desktop) kern.

Doel: rookproef-tool op de geporteerde kern, los van de PySide6-UI. Subcommando's:
  python -m rcm_core.cli validate           project.rcm.json
  python -m rcm_core.cli impact             project.rcm.json
  python -m rcm_core.cli run                project.rcm.json [--full] [--no-parallel|--parallel]
  python -m rcm_core.cli fit                project.rcm.json FM-001 [faaltijd1 ...]
  python -m rcm_core.cli bibliotheek-toon   project.rcm.json
  python -m rcm_core.cli bibliotheek-opslaan project.rcm.json entiteit_id bibliotheek_id omschrijving

Niet meegeporteerd vanuit RCM1: Streamlit-`serve`, Excel-import/export, Monte Carlo,
killer/olifant-classificatie. Zie `RCM2_REFERENTIE.md` (scrub-list).
"""
from __future__ import annotations

import argparse
import os
import sys


def _resolve_parallel_execution(args: argparse.Namespace) -> bool:
    """Bepaal of parallelle verwerking gebruikt moet worden.

    Veiligheidsbeleid:
    - --no-parallel forceert sequentieel.
    - --parallel forceert parallel.
    - Op Windows is de default sequentieel om pool-/DLL-geheugenproblemen te vermijden.
    - Op andere platformen blijft default parallel.
    """
    if getattr(args, "no_parallel", False):
        return False
    if getattr(args, "parallel", False):
        return True
    if sys.platform.startswith("win"):
        return False
    return True


def _prepare_parallel_env(parallel: bool) -> None:
    if not parallel:
        return
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")


def cmd_validate(args: argparse.Namespace) -> int:
    from rcm_core.persistence import load_project
    from rcm_core.validators import validate_project, validate_aannamen

    project = load_project(args.project)
    errors = validate_project(project)
    if errors:
        print(f"Validatie mislukt: {len(errors)} fout(en)")
        for e in errors:
            print(f"  {e}")
        return 1

    warnings = validate_aannamen(project)
    if warnings:
        print(f"Structuur OK — {len(warnings)} aanname-waarschuwing(en):")
        for w in warnings:
            print(f"  {w}")
    else:
        print(f"OK — project '{args.project}' is geldig en volledig gedocumenteerd.")
    return 0


def cmd_impact(args: argparse.Namespace) -> int:
    from rcm_core.cache import find_affected_fms, load_cache_snapshot
    from rcm_core.persistence import load_project

    project = load_project(args.project)
    snap = load_cache_snapshot(project, args.project)
    if snap.cache_file_existed and not snap.global_layer_trusted:
        print(
            "Let op: cache heeft geen geldige globale digest (of project wijkt); "
            "incrementele run herberekent alle faalwijzen."
        )
    affected = find_affected_fms(project, snap.hashes)

    total = len(project.faalwijzes)
    n = len(affected)

    if not affected:
        print(f"Geen gewijzigde faalwijzen (van {total} totaal). Cache is actueel.")
        return 0

    print(f"{n} van {total} faalwijzen zijn gewijzigd:")
    for fm_id in sorted(affected):
        fm = project.faalwijzes[fm_id]
        print(f"  {fm_id}: {fm.faalwijze_omschrijving}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from rcm_core.incremental_run import run_incremental_analysis
    from rcm_core.persistence import load_project
    from rcm_core.validators import validate_project

    project = load_project(args.project)

    errors = validate_project(project)
    if errors:
        print(f"Validatie mislukt — run geannuleerd ({len(errors)} fout(en)):")
        for e in errors:
            print(f"  {e}")
        return 1

    parallel = _resolve_parallel_execution(args)
    _prepare_parallel_env(parallel)

    if args.full:
        print("Volledige herberekening gestart...")
        if not getattr(args, "parallel", False) and sys.platform.startswith("win") and not args.no_parallel:
            print("Info: Windows default gebruikt sequentiele berekening (gebruik --parallel voor opt-in).")
        result = run_incremental_analysis(
            project,
            args.project,
            full_recompute=True,
            parallel=parallel,
        )
    else:
        def _before_analytical(affected: list[str]) -> None:
            print(
                f"Incrementele berekening: {len(affected)} van {len(project.faalwijzes)} faalwijzen..."
            )
            if not getattr(args, "parallel", False) and sys.platform.startswith("win") and not args.no_parallel:
                print(
                    "Info: Windows default gebruikt sequentiele berekening (gebruik --parallel voor opt-in)."
                )

        result = run_incremental_analysis(
            project,
            args.project,
            full_recompute=False,
            parallel=parallel,
            before_analytical=_before_analytical,
        )
        if result.cache_only:
            print("Cache actueel - geen berekening nodig.")

    _print_summary(result.pbs_results)
    return 0


def _print_summary(pbs_results: dict) -> None:
    """Toon PBS-resultaten gesorteerd op kosten. Geen labels: gebruiker leidt
    interpretatie zelf af uit de cijfers (zie scrub-list)."""
    ranked = sorted(pbs_results.values(), key=lambda r: r.total_cost_eur, reverse=True)
    sep = "-" * 75
    print(f"\n{sep}")
    print(f"{'PBS-ID':<12} {'Bouwdeel':<25} {'Falingen':>9} {'Kosten (EUR)':>13} {'Onbeschikb%':>12}")
    print(sep)
    for r in ranked:
        print(
            f"{r.pbs_id:<12} {r.bouwdeel_naam:<25} "
            f"{r.total_expected_failures:>9.2f} "
            f"{r.total_cost_eur:>13,.0f} "
            f"{r.unavailability_pct:>11.3f}%"
        )
    print(sep)
    total_cost = sum(r.total_cost_eur for r in pbs_results.values())
    total_failures = sum(r.total_expected_failures for r in pbs_results.values())
    print(f"{'TOTAAL':<12} {'':<25} {total_failures:>9.2f} {total_cost:>13,.0f}")


def cmd_fit(args: argparse.Namespace) -> int:
    from rcm_core.fitting import fit_from_failure_times

    failure_times = [float(t) for t in args.failure_times]
    result = fit_from_failure_times(failure_times, distribution=args.distribution)
    print(f"Fit resultaat ({result.method}):")
    print(f"  Verdeling : {result.distribution}")
    print(f"  MTTF      : {result.mttf:.2f} jaar")
    if result.sigma > 0:
        print(f"  Sigma     : {result.sigma:.2f} jaar")
    print(f"  AICc      : {result.goodness_of_fit:.2f}")
    print(f"  N         : {result.n_samples} observaties")
    return 0


def cmd_bibliotheek_opslaan(args: argparse.Namespace) -> int:
    from rcm_core.persistence import load_project, save_project

    project = load_project(args.project)
    try:
        items = project.sla_op_als_bibliotheek(
            entiteit_id=args.entiteit_id,
            bibliotheek_id=args.bibliotheek_id,
            omschrijving=args.omschrijving,
            overschrijf=args.overschrijf,
        )
    except ValueError as e:
        print(f"Fout: {e}")
        return 1

    save_project(project, args.project)
    for item in items:
        print(f"Bibliotheekitem aangemaakt/bijgewerkt: [{item.bibliotheek_id}] {item.omschrijving}")
    return 0


def cmd_bibliotheek_toon(args: argparse.Namespace) -> int:
    from rcm_core.persistence import load_project

    project = load_project(args.project)
    if not project.bibliotheek:
        print("Bibliotheek is leeg.")
        return 0
    print(f"Bibliotheek — {len(project.bibliotheek)} items:\n")
    for item in project.bibliotheek.values():
        print(f"  [{item.bibliotheek_id}] ({item.categorie}) {item.omschrijving}")
        print(f"    Waarde   : {item.waarde}")
        if item.bron:
            print(f"    Bron     : {item.bron}")
        if item.toelichting:
            print(f"    Toelichting: {item.toelichting[:100]}")
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rcm",
        description="RCM2 desktop — kern-CLI (rookproef-tool, geen UI)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Valideer project zonder berekening")
    p_val.add_argument("project", help="Pad naar .rcm.json bestand")

    p_imp = sub.add_parser("impact", help="Toon gewijzigde faalwijzen t.o.v. cache")
    p_imp.add_argument("project", help="Pad naar .rcm.json bestand")

    p_run = sub.add_parser("run", help="Bereken (gewijzigde) faalwijzen")
    p_run.add_argument("project", help="Pad naar .rcm.json bestand")
    p_run.add_argument("--full", action="store_true", help="Forceer volledige herberekening")
    p_run.add_argument("--no-parallel", action="store_true", help="Schakel parallelle verwerking uit")
    p_run.add_argument("--parallel", action="store_true", help="Forceer parallelle verwerking (opt-in op Windows)")

    p_fit = sub.add_parser("fit", help="Fit MTTF/sigma uit historische faaltijden")
    p_fit.add_argument("project", help="Pad naar .rcm.json bestand (niet gebruikt, voor consistentie)")
    p_fit.add_argument("fm_id", help="FM-ID (informatief)")
    p_fit.add_argument("failure_times", nargs="+", help="Faaltijden in jaren")
    p_fit.add_argument("--distribution", choices=["normal", "exponential", "auto"], default="auto")

    p_bib = sub.add_parser("bibliotheek-opslaan", help="Sla model-item op als bibliotheekitem")
    p_bib.add_argument("project", help="Pad naar .rcm.json bestand")
    p_bib.add_argument("entiteit_id", help="ID van faalwijze, PM-taak, PBS-item of effectklasse")
    p_bib.add_argument("bibliotheek_id", help="Nieuw bibliotheek-ID")
    p_bib.add_argument("omschrijving", help="Mensleesbare beschrijving")
    p_bib.add_argument("--overschrijf", action="store_true", help="Overschrijf bestaand item")

    p_bibt = sub.add_parser("bibliotheek-toon", help="Toon alle bibliotheekitems")
    p_bibt.add_argument("project", help="Pad naar .rcm.json bestand")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "validate": cmd_validate,
        "impact": cmd_impact,
        "run": cmd_run,
        "fit": cmd_fit,
        "bibliotheek-opslaan": cmd_bibliotheek_opslaan,
        "bibliotheek-toon": cmd_bibliotheek_toon,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
