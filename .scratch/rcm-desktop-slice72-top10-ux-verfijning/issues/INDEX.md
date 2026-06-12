# Slice 72 — issues

**PRD:** [PRD.md](../PRD.md)  
**Status:** **goedgekeurd** — GitHub publicatie pending ([GITHUB_PUBLISH.md](../GITHUB_PUBLISH.md))

| # | Title | Type | Triage | Blocked by | GitHub |
|---|--------|------|--------|------------|--------|
| [00](00.md) | NB-effectfilter dropdown opent bij klik | AFK | ready-for-agent | slice 71 | done lokaal |
| [01](01.md) | Faalwijze standaard; Component-bron verwijderen | AFK | ready-for-agent | — | done lokaal |
| [02](02.md) | Top 10 chart-only (tabel verwijderen) | AFK | ready-for-agent | — | done lokaal |
| [03](03.md) | Staaflabels volgen metric en uren/%-weergave | AFK | ready-for-agent | 05 | done lokaal |
| [04](04.md) | NB-effectfilter end-to-end op Top 10 bijdragen | AFK | ready-for-agent | 00, 03 | done lokaal |
| [05](05.md) | Display-seam bijdragen-waarden | AFK | ready-for-agent | — | done lokaal |

## Implementatievolgorde

1. **00** (P0 — filter bruikbaar)
2. **05** → **03** (display-seam vóór chart-labels)
3. **01**, **02** (parallel mogelijk na 00)
4. **04** (regressie + e2e na 00 + 03)

## GitHub publiceren

```powershell
gh auth login
.\.scratch\rcm-desktop-slice72-top10-ux-verfijning\publish-issues.ps1
```

## Start

```
/tdd slice 72 issue 00
```
