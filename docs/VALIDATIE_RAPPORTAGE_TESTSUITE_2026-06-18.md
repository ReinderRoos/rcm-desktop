# Validatie-rapportage — testsuite (2026-06-18)

**Datum:** 2026-06-18  
**Branch:** `feat/workspace-rapportage-slice58`  
**HEAD:** `1afc532` (Cursor agent-skills, diagnostiekscript en referentiedocumenten)  
**Commando:** `python -m pytest --tb=no -q` (1 run, 6:38 min)

---

## Statistisch overzicht

| Uitkomst | Aantal |
|---|---|
| Passed | 1464 |
| Failed | **0** |
| Skipped | 8 |
| Deselected (`-m 'not perf'`) | 13 |

**0 echte faluren.** Alle 8 skips zijn gedocumenteerde uitzonderingen — zie indeling hieronder.

---

## Indeling skips

| Categorie | # skips | Aard |
|---|---|---|
| Model-keuze / intentioneel ontwerp | 6 | Geen actie nodig |
| Actieverpunt (ontbrekende afhankelijkheid) | 2 | **Fix venv** |

---

## Model-keuzes — geen bugs (6 skips)

### Top 10 modus verwijderd — slice 104 (2 skips)

| Test | Regel |
|---|---|
| `test_bijdragen_modus_renders_top_n_contribution_rows_after_run` | :442 |
| `test_bijdragen_defaults_to_faalwijze_grouping` | :488 |

**Mecanisme:** `@pytest.mark.skip(reason="Top 10 modus verwijderd (slice 104)")`  
**Oordeel:** Tombstone-skip voor feature die bewust is verwijderd in slice 104. Tests documenteren verwijderd gedrag en kunnen op termijn worden weggefreesd wanneer slice 104 definitief is geëtiketteerd.

### Gaarkeuken CM/PM-fixture ontbreekt (3 skips)

| Test | Bewaakte fixture |
|---|---|
| `test_gaarkeuken_cm_fixture_has_random_sigma_inconsistency` | `RCMCostdata export_Gaarkeuken_CM.rcm.rcm.json` |
| `test_gaarkeuken_cm_validate_service_reports_invalid` | `RCMCostdata export_Gaarkeuken_CM.rcm.rcm.json` |
| `test_gaarkeuken_cm_repair_via_pm_normalization` | beide CM + PM fixtures |

**Mecanisme:** `@pytest.mark.skipif(not file.is_file(), reason=...)`  
**Oordeel:** Klantfixtures die niet in de repo zitten (privacy/omvang). Conditional skip is de juiste aanpak — tests draaien automatisch zodra de fixtures lokaal aanwezig zijn.

### Symlinks niet ondersteund op Windows (1 skip)

| Test | Bestand |
|---|---|
| `test_scan_skips_symlink` | `test_portfolio_scan.py:54` |

**Mecanisme:** `except OSError: pytest.skip("symlinks not supported on this platform")`  
**Oordeel:** Platform-guard. Windows vereist verhoogde rechten voor symlinks; de aanpak via `try/except OSError` is de juiste platformneutrale patroon. Geen actie nodig.

---

## Actieverpunt (2 skips)

### matplotlib niet geïnstalleerd (2 skips)

| Test | Bestand |
|---|---|
| `test_write_report_docx_creates_parseable_file` | `test_report_docx_writer.py` |
| alle tests | `test_report_materialization_service.py` |

**Mecanisme:** `pytest.importorskip("matplotlib")` — module-level soft skip  
**Root cause:** `matplotlib>=3.8` werd in dit branch toegevoegd aan `[project].dependencies`
(commit `c3645c8`, slice 57/58), maar de venv is niet bijgewerkt na die wijziging.

**Actie:**
```
pip install -e ".[dev]"
```
of minimaal:
```
pip install "matplotlib>=3.8"
```
Na installatie draaien beide testmodules automatisch mee in de standaardsuite.

---

## Deselected (13 tests)

Perf-gemarkeerde tests worden uitgesloten via `addopts = "-ra -m 'not perf'"` in `pyproject.toml`.
Dit is configuratie, geen skip — ze draaien op aanvraag via `pytest -m perf`.

---

## Conclusie

**De suite is schoon: 1464 passed, 0 failed.**  
Van de 8 skips zijn er 6 intentioneel (tombstone, klantfixtures, platform-guard).  
Het enige concrete actieverpunt is de venv bijwerken na toevoeging van matplotlib in dit branch.

| Verdeling | # |
|---|---|
| Bugs | 0 |
| Model-keuze / intentioneel | 6 |
| Actieverpunt venv | 2 (1 root cause) |
