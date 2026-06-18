# HILT107 — Werkruimte chrome-layout v2 (+ 107-B/108/109)

**Datum:** 2026-06-18  
**Analist:** Reinder  
**Build/branch:** lokaal (pre-merge)  
**Fixture:** awzi_haarlem_waarderpolder_demo

## Checklist slice 107

| # | Onderdeel | GO | NOK | Notities |
|---|-----------|:--:|:---:|----------|
| 1 | Navigatierail rechts (~160px); Input/Output onder elkaar | x | | GO; polish: tabs rechts uitlijnen; Input-view-tabs tussen Input- en Output-kop |
| 2 | Rail-labels Output: KPI, LCC, LTAP, TopX | x | | |
| 3 | Rail-labels Input: Faalwijzen, REV, Effect, Taakgroep, Correctief | x | | v2.1 volledige labels (ADR-0021) |
| 4 | Meer chart/tabel-hoogte vs oude subnav_row | x | | impliciet OK (niet expliciet vergeleken) |
| 5 | Chrome-footer alleen onder detail_zone | x | | |
| 6 | Footer links: context/view-naam | — | | **Superseded ADR-0021:** context verplaatst naar view-titel |
| 7 | Footer midden: metric/horizon/NB (TopX/LCC) | x | | |
| 8 | Footer rechts: vaste kolom; LCC types verticaal | x | | |
| 9 | LCC what-if licht in footer | x | | |
| 10 | Meekoppelkansen boven grafiek (inhoud) | x | | |
| 11 | KPI via rail + Ctrl+K; geen Beeld-toggle | x | | |
| 12 | Top bijdragen menu-label; TopX in rail | x | | |
| 13 | Sticky view per zijde | x | | |
| 14 | Delta Pi huisstijl rail + footer | x | | |
| 15 | Geen Top-10-view terug | x | | |

## Checklist slice 107-B / 108 / 109 (ADR-0021)

| # | Onderdeel | GO | NOK | Notities |
|---|-----------|:--:|:---:|----------|
| B1 | View-titel prominent boven detail_zone | x | | |
| B2 | Footer twee zones (geen context links) | x | | |
| 108-1 | Enkele selectie opent inspector niet | x | | |
| 108-2 | Dubbelklik opent inspectiemodus | x | | |
| 108-3 | Tabel max. 3 rijen context | x | | |
| 108-4 | LCC-plot per faalwijze in inspector | x | | |
| 108-5 | Plot volgt metric-wijziging footer | x | | |
| 108-6 | Pijl omhoog/omlaag navigeert FM | x | | |
| 108-7 | Diagram-toggle sluit inspector | x | | |
| 109-1 | Top bijdragen dubbelklik → inspector only | x | | |
| 109-2 | Bewerken… → faalwijze-editor | x | | |
| 109-3 | Input → Faalwijzen dubbelklik → editor | x | | |

## Kanttekeningen (non-blocking)

1. **Rail layout polish:** tabnamen rechts uitlijnen; Input-view-tabs tussen Input-kop en Output-kop plaatsen (niet alle tabs onder beide koppen).
2. Item 4 (hoogte vs subnav_row) niet side-by-side vergeleken — impliciet akkoord.

## Eindoordeel

- [x] **GO** — slice 107 + 107-B/108/109 mergebaar
- [ ] **GO met kanttekening** — issue(s): …
- [ ] **NO-GO** — blockers: …
