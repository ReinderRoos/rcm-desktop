# PRD — RCM2 desktop slice 64 (portfolio-merge: scan + library distill)



**Status:** done (issues 01–04 af)  

**Versie:** 1.1  

**Parent:** ADR-0009; grill 4+5; epic `.scratch/rcm-desktop-epic-parity-portfolio-mc/`  

**Datum:** 2026-06-05



## Problem Statement



MNN BAP heeft ~13 netwerkschakel-modellen. Analisten willen uniformiteit controleren en een

faalwijze-library met bronvermelding, zonder modellen stil samen te voegen. v1 leest alleen

lokaal gesynchroniseerde mappen; dedup is technisch (fingerprint), niet op vrije tekst.



## Done



- ADR-0009 accepted

- `portfolio_manifest.py`, `portfolio_scan.py`, `library_distill.py`

- `portfolio_merge.py` — merge onder fictieve top-PBS + sidecar

- `portfolio_run.py` — submodel cache-partitionering

- `BibliotheekItem.provenance`

- Desktop wizard + library explorer

- Unit + gate tests



## User stories



1. Als analist wil ik een sync-root kiezen en netwerkschakels auto-detecteren. **done**

2. Als analist wil ik een portfolio `.rcm.json` met fictieve top-PBS en prefixed IDs. **done**

3. Als analist wil ik per submodel aparte cache/run (performance). **done**

4. Als analist wil ik een library explorer met N-bronnen badge en variant clusters. **done**



## Issue-volgorde



| # | Titel | Status |

|---|-------|--------|

| 00 | ADR + scan + distill kern | **done** |

| 01 | `portfolio_merge.py` (2-fixture POC) | **done** |

| 02 | Submodel cache-partitionering | **done** |

| 03 | Desktop wizard (QFileDialog + preview) | **done** |

| 04 | Library explorer UI | **done** |



## Testcommando



```powershell

python -m pytest tests/test_portfolio_manifest.py tests/test_portfolio_scan.py tests/test_library_distill.py tests/test_portfolio_merge.py tests/test_portfolio_run.py tests/test_portfolio_wizard_service.py tests/test_portfolio_wizard_dialog.py tests/test_library_explorer_service.py tests/test_library_explorer_dialog.py tests/test_slice64_portfolio_gate.py -q

```

