# HILT96 — Modelvergelijking v1 acceptance gate

**Status:** GO (2026-06-18)  
**Blocked by:** issues 01–05 (AFK done)  
**Analist:** Reinder Roos  
**Datum:** 2026-06-18  
**Project A (baseline):** klantproject (paar 1 + paar 2)  
**Project B (scenario):** klantproject (paar 1 + paar 2)  

## Checklist (issue 06)

Handmatige QA op **twee echte klantprojecten**:

| # | Check | Project 1 | Project 2 | Opmerking |
|---|-------|-----------|-----------|-----------|
| 1 | **Read-only** — geen uniformeren-UI; geen stille modelwijziging | [x] | [x] | |
| 2 | **Dual load** — baseline A + scenario B laden zonder portfolio | [x] | [x] | |
| 3 | **FM-uitlijning** — id, fingerprint, alleen-A/B herkenbaar | [x] | [x] | |
| 4 | **Balanced split** — invoer én resultaten per FM even zichtbaar | [x] | [x] | Resultaten lastig te interpreteren (non-blocking) |
| 5 | **Invoerverschillen** — schema-velden gemarkeerd; exclusions voelbaar correct | [x] | [x] | |
| 6 | **Resultaatverschillen** — cache-hydrate; Run A/B/both; US16 side-by-side | [x] | [x] | |
| 7 | **Visuele taal** — A/B-kleuren, badges, diff-highlight, status-strip | [x] | [x] | |
| 8 | **Geen shell-integratie** — compare alleen via vergelijkingswerkruimte-entry | [x] | [x] | |

## Besluit

- [x] **GO** — slice 96 mag op done
- [ ] **NO-GO** — blockers:

### Blockers (indien NO-GO)

_…_

## Productinzicht (post-HILT → besluit analist)

Vergelijking tussen twee modellen moet **niet primair op `fm_id`**.

**Besluit:** apart veld **`library_id`** op faalwijze (niet hergebruiken
`library_ref`):

| Veld | Rol |
|------|-----|
| `library_ref` | FK naar bibliotheek-item *in dit project* (faalmodel-bron) |
| `library_id` | Stabiele correlatie-ID over modelleringen/projecten; optioneel; bewerkbaar maar bedoeld om ongewijzigd mee te kopiëren |

- **Uitlijning (slice 97+):** match op gelijke niet-lege `library_id` vóór fingerprint.
- **Uniformeren:** modelparameter-Δ (invoer, geen output) na library-id-match.

Huidige slice 96: `fm_id` → fingerprint; geen `library_id` in model yet.

→ Volgende stap: domeinveld + copy-regels + compare-alignment (slice 97 / grill).
