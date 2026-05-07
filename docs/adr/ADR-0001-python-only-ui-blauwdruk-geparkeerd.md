# ADR-0001 — Python-only UI-stack voor RCM2 v1; React Web-UI-blauwdruk geparkeerd

## Status
Accepted

## Datum
2026-05-07

## Context
RCM1 bevat een gedetailleerde React Web-UI implementatieblauwdruk
(`../rcm/RCM_WEB_UI_IMPLEMENTATIEBLAUWDRUK.md`) en heeft via issues 12-14
een React PBS-tree-component opgeleverd. Bij de start van RCM2 is gevraagd of
deze blauwdruk de basis moet zijn.

## Beslissing
Voor RCM2 v1 wordt **geen React Web-UI** gebouwd. De UI is een **Python-only
desktop-app** (zie ADR-0002). De Web-UI-blauwdruk wordt **geparkeerd** als
langetermijnvisie, niet uitgesloten.

## Overwegingen
- Multi-user / server-deploy is voor RCM2 v1 gedegradeerd van WON'T (RCM1 v1)
  naar **COULD**. Daardoor verdwijnt de hoofdreden voor een netwerkgrens
  tussen UI en kern.
- De Pure UI-swap heeft als doel: andere look-and-feel, niet ander
  deploymentmodel. Een desktop-app levert die look-and-feel direct.
- React PBS-tree-component (issues 12-14 in RCM1) is niet herbruikbaar in
  een Python-stack zonder embedded React; de kosten daarvan zijn niet
  gerechtvaardigd voor v1.

## Consequenties
- `RCM_WEB_UI_IMPLEMENTATIEBLAUWDRUK.md` wordt niet als basis gebruikt;
  blijft als referentie staan voor toekomstige overweging.
- Multi-user/web-deploy is niet ingebouwd in v1; pas heroverwegen wanneer
  multi-user van COULD naar SHOULD/MUST schuift.

## Trigger voor heropening
- Gebruikersvraag naar gelijktijdig multi-user gebruik;
- of behoefte aan web-deployment over teams heen.

## Gerelateerd
- ADR-0002 (PySide6 als UI-framework).
- `../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md` (keuze 3a).
