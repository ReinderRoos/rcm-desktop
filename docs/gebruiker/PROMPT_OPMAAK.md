# Prompt — opgemaakte gebruikershandleiding (Claude)

Kopieer onderstaande prompt naar Claude (claude.ai of Claude Code), voeg de bijlagen toe, en vraag om een **Word- of PDF-document**.

## Bijlagen meegeven

1. **`docs/gebruiker/HANDLEIDING.md`** (volledige tekst of upload)
2. **Alle PNG’s** uit `docs/gebruiker/screenshots/` (01 t/m 08)
3. Optioneel: **`CONTEXT.md`** (alleen als Claude termen moet verifiëren — niet in einddocument opnemen)

---

## Prompt (kopieer vanaf hier)

```text
Je bent technical writer voor industriële assetmanagement-software.

Maak een professionele, Nederlandstalige gebruikershandleiding voor maintenance engineers op basis van de bijgevoegde HANDLEIDING.md en de screenshot-PNG’s.

### Doel
- Leesbaar document voor engineers die RCM al kennen, maar RCM2 desktop nieuw is.
- Geschikt voor export naar PDF en print (A4).

### Bronnen
- Structuur en tekst: HANDLEIDING.md (leidend; mag inkorten of uitbreiden waar nodig voor vloeiende proza).
- Plaatjes: screenshots/01 t/m 08 — plaats op de logische plek bij de genoemde secties; nummer figuren (Figuur 1, 2, …) met korte onderschrift in het Nederlands.
- Versie in document: RCM2 desktop v0.1.0, status “in ontwikkeling” (prominent in voorwoord).

### Opmaak (verplicht)
- Voorblad: titel, ondertitel “Maintenance engineer”, versie, datum, disclaimer tool-in-ontwikkeling.
- Inhoudsopgave met paginanummers.
- Hoofdstukken volgens HANDLEIDING §1–16; Deel A en Deel B duidelijk gescheiden.
- Glossarium als tabel (§3).
- FAQ als tabel (§12).
- Callout-box voor §10.5 (werkruimte vs. rapport) — visueel opvallend (kader of icoon).
- Quick start (§4) als genummerde checklist met afvinkvakjes.
- Appendix’s kleiner lettertype of achterin.
- Footer op elke pagina: “RCM2 desktop v0.1.0 — {datum} — Screenshots v0.1.0”.
- Lettertype: sans-serif (bijv. Calibri of Arial), 11 pt body, 14–18 pt koppen.
- Kleuren spaarzaam: donkergrijs tekst, één accentkleur voor koppen (bijv. #1a5276).

### Inhoudelijke regels
- Geen killer/olifant-terminologie (verwijderd in RCM2).
- UI-labels exact zoals in screenshots (Top 10, Tijdsplot, FM-detail, Rapport genereren…, Componenten).
- Geen verzonnen knoppen of menu’s die niet in de bron staan.
- Waar HANDLEIDING “{…}” placeholders heeft: laat leeg of markeer “invullen door organisatie”.
- Rapport-sectie: benadruk dat standaardrapport projectbreed is.

### Deliverable
1. Volledig document in Markdown (geschikt voor Pandoc/Word).
2. Korte lijst “Figuur → bestandsnaam” mapping.
3. Suggestie voor 1-pagina “snelreferentie” achteraan (optioneel).

Lever geen code; alleen het handleiding-document en figuurlijst.
```

---

## Tips na generatie

- Controleer of alle **8 figuren** zijn opgenomen.
- Vergelijk UI-labels met een actuele build; bij drift screenshots opnieuw genereren:
  `python scripts/capture_gebruikershandleiding_screenshots.py`
- Export naar Word: upload Claude-markdown naar Word, of `pandoc -o handleiding.docx`.
