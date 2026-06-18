## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/9

## What to build

Volledige generatie-ervaring: `ReportGenerationDialog` met PDF-checkbox (default aan), drempels NB/kosten, opt-in functies onder drempel, PBS dee-dive (subtree-relatieve drempels), read-only preview (single vs compare, aantal NB-/kosten-pagina's). `ReportRunner` op achtergrond met busy/progress. `ReportPdfExporter` (docx → PDF via LibreOffice); bij PDF-fout behoud docx + waarschuwing, Word alsnog openen.

Tooltips: rapport standaard projectbreed; UI-filters niet overgenomen.

## Acceptance criteria

- [ ] Dialoogvelden: pad, PDF, drempels, below-threshold, PBS dee-dive, preview counts
- [ ] `ReportEligibilityService.preview_counts` voedt read-only preview
- [ ] `ReportRunner` blokkeert UI niet; voortgang zichtbaar
- [ ] PDF optioneel; default aan; failure laat docx intact + waarschuwing
- [ ] PBS dee-dive past drempels toe t.o.v. subtree
- [ ] Tooltips over scope en filters
- [ ] CI: PDF-export gemockt; docx-pad getest

## Blocked by

https://github.com/ReinderRoos/rcm-desktop/issues/14
