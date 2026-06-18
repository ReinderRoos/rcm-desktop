# Slice 68 — Parity run alignment (handoff)

**Status:** done  
**Datum:** 2026-06-05  
**PRD:** `.scratch/rcm-desktop-slice68-parity-run-alignment/PRD.md`  
**Analyse:** `.scratch/rcm-desktop-slice68-parity-run-alignment/ANALYSE_VALIDATIE_FALEN5.md`

## Probleem

Na slice 67 was CM-overlay alignment bewezen in unit tests (`materialize_cm_overlay_project`), maar de **desktop run-keten** materialiseerde `aw_disabled_pm_ids` niet standaard. Validatie-export toonde 25× C1 ("Run met CM-overlay materialiseren") terwijl counterfactual `ef_cm_overlay` wel klopte.

## Oplossing

1. **Issue 01** — `run_service._resolve_run_project`: default CM-overlay uit import wanneer geen actieve what-if overlay; actieve overlay zonder disabled = analist keuze (alle PM's).
2. **Issue 02** — E2E regressie: `run_service.run` → `build_failure_validation_report`, median `|Δ scenario| < 0.01`, 0× C1-actie.
3. **Issue 03** — Falen5-analyse vastgelegd in `ANALYSE_VALIDATIE_FALEN5.md`.
4. **Issue 04** — A1-dominante rijen: actie "Accepteren: vergelijk met AW-band …; geen softwarefix", grijze markering i.p.v. rood.
5. **Issue 05** — B3-secundair: actie "Optioneel: harmoniseer leeftijd met AW InitialAge (invoer)".

`CACHE_INPUTS_VERSION` → **109** (run-pad materialisatie).

## Analist playbook (post slice 68)

1. Herimport AW Excel (CM-export).
2. Run (validate of werkruimte — beide CM-aligned via `run_service`).
3. Validatie-export:
   - **~0×** "Run met CM-overlay materialiseren" (C1 opgelost)
   - **~79×** A1 band-accepteren (model-keuze, geen bug)
   - **~15×** Parity OK
4. Optioneel: `aw_mc_lifecycle_horizon` voor A2-residu (slice 67 playbook).

## Reproduceerbare checks

```bash
pytest tests/test_slice68_parity_run_alignment.py -q
pytest tests/test_desktop_run_service.py -q
pytest tests/test_failure_validation_export.py -q
pytest tests/test_slice67_parity_rekenbugs.py -q
pytest tests/test_gaarkeuken_parity_gate.py -q
```

Verwachting: alle groen; C1-actie-count = 0 op verse Gaarkeuken run + export.

## Relatie eerdere slices

| Slice | Effect |
|-------|--------|
| 66 | REV-survival bugfix — geen explosieve fails |
| 67 | repair_quality, CM-overlay helper, audits |
| 68 | Run-pad alignment + A1/B3 export UX |
