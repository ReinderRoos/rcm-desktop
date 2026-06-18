# PRD — RCM2 desktop slice 18 (tooltip-zichtbaarheid en tabelweergave)

**Status:** done  
**Versie:** 1.0  
**Triage-labels:** done

## Problem Statement

Tooltips zijn voor gebruikers onzichtbaar of nauwelijks bruikbaar (o.a. door een onvolledig globaal stylesheet op `QToolTip`). Faalwijzen-, FM-resultaten- en LTAP-detailtabellen zijn lastig te scannen: kolommen staan vooral op `Stretch`, waardoor inhoud niet natuurlijk meeschaaalt met tekstlengte; lange teksten zijn niet standaard afgebroken over meerdere regels en er is geen globale weergave-optie om dat uit te zetten.

## Solution

1. Tooltip-presentatie herstellen door het tooltip-stylesheet volledig te stylen (minimaal achtergrond- en tekstkleur, rand), met een rustige professionele uitstraling (richting donkere tooltip met lichte tekst).
2. Gemeenschappelijke tabellen-UX voor de drie tabellen: kolommen primair naar inhoud, met **begrensde** breedtes op brede tekstkolommen (clamp + `Interactive` waar PySide6 geen per-kolom maximum heeft) en laatste kolom die resterende ruimte opvult.
3. Tekstomloop standaard aan, met één toggle in de rechter toolbargroep; voorkeur bewaren in bestaande app-instellingen (`QSettings`), default aan.
4. Bij gewijzigde data rijhoogtes automatisch bijwerken waar nodig wanneer omloop aan staat.
5. Faalwijzen-itemdelegate aanpassen zodat gewone tekstcellen omloop respecteren; FK/editor-kolommen mogen pragmatisch single-line blijven.

## User Stories

1. Als analist wil ik zichtbare tooltips op knoppen en relevante velden, zodat ik begrijp wat elke actie doet zonder documentatie.
2. Als analist wil ik tooltips die duidelijk leesbaar zijn (contrast, padding), zodat lange uitleg niet vermoeiend is.
3. Als analist wil ik dat kolombreedtes aansluiten bij inhoud, zodat ik minder horizontaal hoef te scrollen.
4. Als analist wil ik een maximum op zeer brede tekstkolommen, zodat één extreem lange regel het scherm niet onbruikbaar breed maakt.
5. Als analist wil ik dat de laatste kolom overgebleven ruimte opvult, zodat het paneel rustig uitlijnt bij verschillende vensterbreedtes.
6. Als analist wil ik tekstomloop standaard aan, zodat omschrijvingen en labels volledig zichtbaar zijn.
7. Als analist wil ik omloop uit kunnen zetten met één schakelaar, zodat ik een compacte enkele-regelweergave kan kiezen.
8. Als analist wil ik dat mijn keuze voor omloop onthouden wordt tussen sessies.
9. Als analist wil ik dezelfde weergave-logica op Faalwijzen-, FM- en LTAP-tabellen, zodat ik één mentaal model heb.
10. Als analist die Faalwijzen bewerkt wil ik dat vrije tekstcellen afbreekbaar zijn bij omloop.
11. Als maintainer wil ik constanten voor kolom-plafonds (compact vs breed) op één plek.
12. Als maintainer wil ik tests die regressies op tooltip-stylesheet en voorkeur-keys vangen.

## Implementation Decisions

- Tooltip-polish-module uitbreiden met expliciete achtergrond-, tekst- en randkleur voor `QToolTip`; professionele donkere tooltip als voorkeursrichting.
- ValidateWindow: centrale helpers voor kolomresize-modi, `wordWrap` op de drie tabellen, en na data-refresh `resizeRowsToContents` wanneer omloop aan staat.
- Kolommen: `ResizeToContents` op niet-laatste kolommen; laatste kolom `Stretch`; twee breedteconstanten; te brede tekstkolommen worden na inhoud geclamped (`clamp_horizontal_section_widths`, daarna `Interactive` + `resizeSection` — geen per-sectie `setMaximumSectionSize` in PySide6).
- Toggle: één checkable toolbutton in de rechter toolbargroep; voorkeur via bestaande `QSettings`-organisatie `("rcm2", "desktop")`; default aan.
- Faalwijzen: delegate aanpassen zodat display-tekst wrap kan volgen; editor/FK-kolommen pragmatisch afgebakend.
- Lichtgewicht bundeling van herhaalde tabellen-setup om copy-paste te vermijden; geen wijzigingen aan `rcm_core`.

## Testing Decisions

- Observable gedrag: stylesheet bevat vereiste tooltip-kleuren/fragmenten; instelling voor omloop wordt gelezen na toggle.
- Waar passend smalle Qt-widget- of flow-tests aansluitend op bestaande `tests/test_desktop_tooltip_polish.py` en `tests/test_desktop_qt_flow.py`.
- Performance-loadtests niet in scope; risico grote FM-resultatensets documenteren.

## Out of Scope

- PBS-resultatenboom (`QTreeView`), compare-paneellijsten, domain model, cache, run-engine, JSON-schema.

## Further Notes

- Risico: `resizeRowsToContents` op zeer grote FM-resultatensets kan traag zijn — eerst implementeren; optimaliseren bij gemeten probleem.
- Issues: `issues/01.md`, `issues/02.md`, `issues/03.md` in deze map.
