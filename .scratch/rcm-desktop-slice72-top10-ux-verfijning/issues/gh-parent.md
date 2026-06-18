## Problem Statement

Na slice 71 is de NB-effectfilter zichtbaar maar niet bruikbaar (popup opent niet). De Bijdragen-toolbar heeft nog een overbodige Component-bron, een redundante tabel naast het staafdiagram, en staaflabels die altijd aandeel-% tonen i.p.v. de gekozen uren/%-weergave. Effectfiltering op bijdragen moet end-to-end verifieerbaar zijn.

## Solution

1. **00** — NB-effectfilter dropdown functioneel (klik opent multi-select)
2. **01** — Faalwijze als standaard bron; Component-toggle verwijderen
3. **02** — Top 10 chart-only (tabel + compare-tabel weg)
4. **05** — Qt-vrije display-seam voor bijdragen-waarden
5. **03** — Staafdiagram-labels via display-seam (metric + uren/%)
6. **04** — Integratietests: effectfilter wijzigt ranking en waarden

## Child issues

| # | Titel | Type | Blocked by |
|---|-------|------|------------|
| 00 | NB-effectfilter dropdown opent bij klik | AFK | slice 71 |
| 01 | Faalwijze standaard; Component-bron verwijderen | AFK | — |
| 02 | Top 10 chart-only (tabel verwijderen) | AFK | — |
| 03 | Staaflabels volgen metric en uren/%-weergave | AFK | 05 |
| 04 | NB-effectfilter end-to-end op Top 10 bijdragen | AFK | 00, 03 |
| 05 | Display-seam bijdragen-waarden | AFK | — |

## PRD

`.scratch/rcm-desktop-slice72-top10-ux-verfijning/PRD.md`

## Labels

`ready-for-agent`
