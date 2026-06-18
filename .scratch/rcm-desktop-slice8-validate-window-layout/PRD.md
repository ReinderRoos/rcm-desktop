# PRD — RCM2 desktop slice 8 (ValidateWindow: compacte topstrip + PBS-boom uitbreiding)

**Status:** deferred (grill-me 2026-05-19)  
**Triage:** ready-for-human  
**Versie:** 1.1  
**Triage-labels:** zie `../../AGENTS.md`

## Bron / context

- Project README, `CONTEXT.md` (domeinvocabulaire), `AGENTS.md` (UI/kern-decoupling,
  adapter-first tests).
- Voorgaande slices: validate-flow, projectpreview, run-contract, FM-resultatentabel,
  PBS-platte tabel (`pbs_rows`), PBS-read-only boom (`build_pbs_tree` /
  `PBSResultsTreeModel`), faalwijzen-grid via tabulaire editing-pipeline.
- Design-interview (layout refactor): vastgelegde beslissingen staan samengevat onder
  *Implementation decisions*.

## Problem statement

Het validatie-/run-scherm voelt **visueel vol**: de **platte PBS-resultatentabel**
neemt ruimte en herhaalt in grote lijnen wat de **PBS-boom** al hiërarchisch toont.
Daardoor is er minder overzicht voor de keten **project → faalwijzen bewerken →
FM-resultaten → PBS-impact**.

Daarnaast staat **projectoverzicht** (preview-tellingen) en **Top-5 faalwijzen**
nu onder elkaar in één kolom, terwijl **analyseresultaat** (`RunResult`) in een
aparte groep lager op het scherm staat. Dat verspreidt de kernstatus over de verticale
as en vraagt scrollen voordat je in één oogopslag ziet: *is het project gevalideerd,
wat zegt de run, en wat zijn de belangrijkste faalwijzen?*

## Solution

1. **Verwijder de PBS-platte tabel uit het ValidateWindow-paneel** — alleen de
   **read-only PBS-boom** blijft voor PBS-resultaten na een geslaagde run met
   niet-lege `pbs_rows`. Zichtbaarheid en reset-discipline blijven gelijk aan de
   huidige PBS-resultatenpaneel-logica (alleen zonder tabelcomponent).

2. **Breid de PBS-boom uit met totalen voor faalmomenten en downtime**, naast de
   bestaande totalen voor niet-beschikbaarheid en kosten. Kolomvolgorde (vast):
   PBS-id → Bouwdeel → **Faalmomenten (totaal)** → **Downtime (uur, totaal)** →
   **Niet-beschikbaarheid % (totaal)** → **Kosten (EUR, totaal)**. Waarden zijn
   **aggregaat-totalen** per knoop (`*_total`-semantiek op `PBSResultRow`), conform
   bestaande DFS/aggregatie in `build_pbs_rows`. De boom blijft **niet sorteerbaar**;
   rangorde = hiërarchie + stabiele sibling-volgorde zoals nu.

3. **Één geünificeerde topstrip (horizontaal)** onder de werkbalk: één groep met
   **drie kolommen**:
   - **Links — Projectoverzicht:** de bestaande preview-tellingen (aantallen PBS-items,
     functies, faalwijzen, PM-taken).
   - **Midden — Dynamische statuskolom:**
     - Zolang er **geen actieve run-presentatie** is die deze kolom claimt: toon
       **validatie-/samenvatting** (`ValidateResult`-teksten zoals nu relevant voor
       de gebruiker na validate).
     - Wanneer een **run actief is of resultaat getoond wordt**: toon **analyse-KPI’s**
       en samenvatting uit `RunResult` (status, kernmetrics zoals totale faalmomenten,
       kosten, enz.) — de inhoud die nu in het aparte analyseresultaat-paneel staat,
       verplaatst naar deze middelste kolom.
   - **Rechts — Top-5 faalwijzen:** de bestaande lijst uit `ProjectPreview`, naast
     het projectoverzicht i.p.v. eronder.

4. **Verticale volgorde van panelen** (boven naar beneden):
   **Werkbalk → geünificeerde topstrip → Faalwijzen-grid (bewerkbaar) →
   FM-resultatentabel → PBS-boom.**

5. **Het aparte onderpaneel “Analyseresultaat” verdwijnt** — er komt **geen**
   tweede verticale blok onder de topstrip voor run-output; alles wat daar thuishoorde
   zit in de **middelste kolom** van de topstrip.

## User stories

### Ruimte en focus

1. Als reliability-analist wil ik **geen dubbele PBS-weergave** (tabel én boom),
   zodat ik schermruimte kan gebruiken voor interpretatie i.p.v. herhaling.
2. Als analist wil ik **één duidelijke PBS-weergave** (de boom), zodat ik
   hiërarchische impact kan lezen zonder tussen een platte tabel te hoeven.

### PBS-boom — inhoud

3. Als analist wil ik in de PBS-boom per knoop **totale faalmomenten** zien,
   zodat ik faalfrequentie-impact langs de PBS-tak kan aflezen.
4. Als analist wil ik in de PBS-boom per knoop **totale downtime (uur)** zien,
   zodat ik storingsduur-impact naast kosten en niet-beschikbaarheid kan plaatsen.
5. Als analist wil ik dat faalmoment-, downtime-, niet-beschikbaarheid- en
   kostenkolommen allemaal **aggregaat-totalen** tonen per knoop, zodat ik takken
   eerlijk kan vergelijken met hetzelfde semantische model als elders in de run-output.
6. Als analist wil ik een **vaste kolomvolgorde** (id → bouwdeel → faalmomenten →
   downtime → NB% → EUR), zodat mijn scanpatroon voorspelbaar blijft.
7. Als analist wil ik dat de boom **niet sorteerbaar** blijft op kolommen,
   zodat de hiërarchische volgorde niet wordt doorbroken.

### Topstrip — lay-out en cognitieve last

8. Als analist wil ik **projectoverzicht, analyse-status en Top-5** in **één**
   horizontale strip zien, zodat ik minder hoef te scrollen voor het globale beeld.
9. Als analist wil ik het **projectoverzicht links**, zodat ik eerst context
   (omvang van het model) zie voordat ik details lees.
10. Als analist wil ik de **Top-5 faalwijzen rechts**, zodat risico-highlights
    direct naast de hoofdstatus staan.
11. Als analist wil ik in het **midden** van die strip de **belangrijkste status**
    van de applicatie zien (validate óf run), zodat mijn aandacht op één plek blijft.

### Topstrip — gedrag validate vs run

12. Als analist wil ik na een **succesvolle validate** (met preview) in het midden
    **validatiesamenvatting** zien, zodat ik weet of het project geladen en consistent is.
13. Als analist wil ik zodra een **run wordt voorbereid of uitgevoerd** en het scherm
    run-output toont, in het midden **analyse-KPI’s** te zien i.p.v. alleen
    validatietekst, zodat ik niet tussen twee verticale blokken hoef te springen.
14. Als analist wil ik bij **validatiefouten** (geen bruikbare preview) een heldere
    **fout-/samenvattingsweergave** in het midden, zodat ik weet wat ik moet fixen
    zonder dat de strip “leeg” aanvoelt.
15. Als analist wil ik dat bij **reset van pad / foutpad / nieuwe validate** de strip
    **netjes terugvalt** naar de juiste face (validate vs run), consistent met de
    bestaande reset-discipline van preview en run-panelen.

### Faalwijzen- en FM-resultatenpaneel

16. Als analist wil ik het **faalwijzen-grid direct onder de topstrip**, zodat
    bewerken logisch volgt op het projectbeeld.
17. Als analist wil ik de **FM-resultatentabel onder het grid**, zodat invoer
    en FM-output dicht bij elkaar blijven.
18. Als analist wil ik de **PBS-boom onderaan**, zodat hiërarchische aggregatie
    als afsluitende aggregatielaag voelt.

### Non-functioneel — architectuur

19. Als onderhouder wil ik dat **views geen directe `rcm_core`-imports** krijgen
    buiten typing; presentatie van strings en formatting blijft via adapter +
    bestaande formatting/message-conventies waar passend.
20. Als tester wil ik dat **adapterlogica** die nieuw of gewijzigd wordt **pytest**
    dekt, en Qt-gedrag via **pytest-qt** op het validate-pad, conform AGENTS.md.

## Implementation decisions

- **Modules om te wijzigen / aan te vullen (conceptueel):**
  - **Validate-window view:** herbouw van de verticale lay-out; verwijderen van de
    PBS-tabel-widget en bijbehorende proxy-model-binding uit dit venster; samenvoegen
    van preview- en run-presentatie in één horizontale **topstrip-groep** met drie
    kolommen; verwijderen van het aparte verticale **analyseresultaat-groepvak**
    onder de strip.
  - **PBS-boom Qt-model:** uitbreiden van kolomdefinities en koppen — mapping naar
    numerieke velden op `PBSResultRow` voor **expected_failures_total** en
    **total_downtime_hr_total**, met NL-weergave consistent met bestaande formatters
    (faalmomenten/downtime/EUR/procent waar van toepassing).
  - **Teksten / i18n:** nieuwe of hergebruikte message-constanten voor groepstitel
    van de geünificeerde strip en voor de nieuwe boomkoppen (faalmomenten, downtime).
  - **State-weergave in middelste kolom:** definieer een eenduidige prioriteit —
    wanneer run-output zichtbaar is (idle/busy/done volgens huidige vensterlogica),
    toon run-KPI’s in het midden; anders toon validate-/preview-teksten. Hergebruik
    bestaande bronobjecten (`ValidateResult`, `RunResult`, `ProjectPreview`) —
    geen wijziging aan het **run-contract** of aan `build_pbs_rows` / boomconstructie
    in de pure adapter, tenzij blijkt dat een veld ontbreekt (uitgangspunt: velden
    bestaan al op `PBSResultRow`).
  - **PBS-platte tabel:** niet meer in deze view hangen; het **optionele** behoud van
    het tabel-model in de codebase voor toekomstig hergebruik is een implementatiekeuze —
    default is **alleen verwijderen uit ValidateWindow** tenzij elders nodig.
  - **Deep module (optioneel):** kleine pure functie(s) die uit `ValidateResult` /
    `RunResult` een **vlakke tekstregel of korte bulletlijst** voor de middelste
    kolom maken — alleen als dat de view merkbaar vereenvoudigt; anders mag de view
    dun blijven met bestaande formatting.

- **Architectuur:** geen Qt in `rcm_core`; adapter blijft grens voor run/preview-data.
  Geen nieuwe persistentie of editing-pipeline-wijzigingen voor deze slice.

- **UX-details:** standaard boom-expand gedrag **ongewijzigd** ten opzichte van slice 6
  (roots uitgeklapt, dieper ingeklapt), tenzij implementatie een regressie signaleert.

## Testing decisions

- **Goede tests** beschrijven **observeerbaar gedrag** via publieke UI-/adapter-API’s,
  niet interne widget-hierarchie-details die bij refactors breken.
- **Te testen (prioriteit):**
  - **PBS-boommodel:** kolomaantal, koppen, en weergave van de twee nieuwe totalen
    (minimaal één node met bekende waarden uit fixtures).
  - **pytest-qt flow (`ValidateWindow`):** PBS-tabel ontbreekt of is niet gebonden;
    PBS-boom nog aanwezig na run; topstrip zichtbaarheid bij preview en bij run;
    middelste kolom toont validate-context vs run-context volgens de gekozen regels;
    geen tweede verticale analyseresultaat-groep onder de strip.
- **Prior art:** bestaande desktop Qt-flowtests en PBS-boom/table-modeltests; patronen
  voor signal spies en `show()` voor visibility volgens eerdere fixes.

## Out of scope

- Nieuwe berekeningen in de kern, wijziging van `PBSResult`/motor-output, of nieuwe
  cache-/digest-semantiek.
- PM/CM-scenario-kolommen op PBS-niveau (toekomstige uitbreiding; niet deze slice).
- Koppeling tussen tabel- en boomselectie (tabel verdwijnt).
- Sorteerbare PBS-boom of export naar Excel.
- Wijziging aan de tabulaire faalwijzen-pipeline zelf (alleen layout/herschikking rond
  het bestaande grid).

## Issues (lokale tracker)

| # | Bestand | Kort | Triage |
|---|---------|------|--------|
| 20 | `issues/20.md` | PBS-boom: zes kolommen — **in codebase geleverd** | done |
| 21 | `issues/21.md` | ValidateWindow close-out (idle_banner, toggle flanken, dode PBS-tabelmodel) | ready-for-human |

## Deferred (grill-me 2026-05-19)

**Waarom uitgesteld:** analisten zochten in ValidateWindow vooral **één faalwijze precies verifiëren**; dat is geen layout-probleem. Standaard product = **resultatenwerkruimte**. FM-spot-check wordt **slice 34** (`rcm-desktop-slice34-fm-verificatie-werkruimte`).

**Wat al live is (geen issue-21-werk meer nodig):**

- Horizontale topstrip met links/midden/rechts en validate/run-faces in het midden.
- PBS-boom met zes kolommen (`PBSResultsTreeModel`).
- Geen platte `PBSResultsTableModel` in ValidateWindow (alleen boom in `pbs_table_group`).

**Resterende close-out (scope A, wanneer herprioriteerd):**

- `idle_banner` verwijderen; status alleen in strip-midden; strip altijd zichtbaar.
- Toggle “Overzicht”: alleen links/rechts verbergen, midden blijft.
- `PBSResultsTableModel` + tests verwijderen; `pbs_table_group` hernoemen naar boom-semantiek.
- **Geen** volledige PRD-re-alignment (lineaire panelvolgorde, FM+PBS tegelijk zonder toggle).

**FM-verificatie:** zie `CONTEXT.md` (na slice 34 issue 01) en slice-34 PRD.

## Further notes

- **Risico’s:** zorg dat **busy/run-in-progress** en **foutpaden** de middelste kolom
  niet leeg of tegenstrijdig tonen t.o.v. de run-knop en worker-status — afstemmen
  op bestaande `_render_run` / reset-paden.
- **Modules & tests:** bij implementatie van issue **21** expliciet kiezen of het
  PBS-tabelmodel uit tests verdwijnt of alleen uit het venster — default: venster en
  boom uitbreiden; tabeltests opruimen als het model nergens meer hangt.
