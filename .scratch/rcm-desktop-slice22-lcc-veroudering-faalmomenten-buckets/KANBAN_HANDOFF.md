# Kanban-handoff — slice 22 LCC aging faalmomenten-buckets (2026-05-22)

**Slice-map:** `.scratch/rcm-desktop-slice22-lcc-veroudering-faalmomenten-buckets/`

## Status

| Issue | Titel | Triage |
|-------|--------|--------|
| 01 | Fase 1 voorwaardelijke normaal | **done** (in `856cab1`) |
| 02 | Fase 2 aging SSOT + Φ-segmenten | **done** (in `856cab1`) |

**Automated:** `tests/test_lcc_profile.py` groen; `expected_aging_lifecycle_faalmomenten_ssot` in `rcm_core/distributions.py`.

## Handmatige check (nog voor jou)

1. Open LCC na run op project met **aging** faalwijzen — piek rond MTTF, niet vlak.
2. Vergelijk met **random** faalwijze — vlak/constant profiel blijft verklaarbaar.
3. Project met `repair_quality < 1` — jaarvorm verschilt van fase‑1‑benadering.
