# HILT104 — Handcheck FM single-run presentatie + Top 10-afbouw



**Issue:** slice 104 issue 05  

**Datum:** 2026-06-17  

**Status:** NO-GO



## Doel



Visuele QA van de vernieuwde **single-run FM-resultatenview**, afwezigheid Top 10,

en direct bewerkbare FM-editor tabs.



## Voorbereiding



1. Start resultatenwerkruimte: `python -m rcm_desktop.main`

2. Open demo-project: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

3. Draai **Start analyse** (analytisch of MC)



## Pad A — Single-run FM presentatie



| # | Check | OK | NOK | Notities |

|---|-------|----|-----|----------|

| A1 | Startup opent op **FM-resultaten** (geen Top 10) | x | | |

| A2 | Tabel is **beknopt**: één metric-kolom + id/bouwdeel | x | | |

| A3 | Metric-wissel (Faalmomenten/NB/Kosten) werkt in tabel | x | | |

| A4 | **NMF/RF** standaard uit; toggle toont kolommen | x | | |

| A5 | **Tabel / diagram** toggle werkt | x | | |

| A6 | Diagram volgt actieve metric + horizon (Ø per jaar) | x | | |

| A7 | Horizon **Levensduur** + jaarkiezer werken in tabel én diagram | x | | |



## Pad B — Geen Top 10



| # | Check | OK | NOK | Notities |

|---|-------|----|-----|----------|

| B1 | Geen **Top 10** modus-knop in toolbar | x | | Eerst NOK: Top 10 nog in dropdown (disabled). Fix: `enabled_views_for_side` — hercheck OK |

| B2 | Scenario compare: geen Top 10 compare-view | x | | OK; vergelijk-view opent geen FM-editor (zie C1) |



## Pad C — FM-editor tabs



| # | Check | OK | NOK | Notities |

|---|-------|----|-----|----------|

| C1 | Dubbelklik FM (willekeurige kolom) opent editor | | x | Single-run: OK. Vergelijk scenario's: editor opent niet |

| C2 | Tab **Effecten**: link toevoegen/wijzigen + opslaan | | x | Effecten-tab niet zichtbaar |

| C3 | Tab **Preventief**: PM-taak bewerken + opslaan | | x | Tab niet zichtbaar of werkt niet |



## Akkoord



| Analist | Uitkomst | Datum |

|---------|----------|-------|

| Reinder | **NO-GO** | 2026-06-17 |



## Blockers (invullen bij NO-GO)



1. **FM-editor Effecten-tab ontbreekt** in single-run view (slice 104 issue 03 AC)

2. **FM-editor Preventief-tab** niet bruikbaar

3. **Dubbelklik FM opent geen editor** in vergelijk-scenario-modus


