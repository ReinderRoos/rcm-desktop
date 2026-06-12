# Gebruikersdocumentatie — maintenance engineer

| Bestand | Doel |
|---------|------|
| [HANDLEIDING.md](HANDLEIDING.md) | Outline + inhoudsskelet (bron voor PDF/Word) |
| [screenshots/](screenshots/) | UI-plaatjes (PNG), gekoppeld aan release |
| [PROMPT_OPMAAK.md](PROMPT_OPMAAK.md) | Prompt voor opmaak in Claude |

## Screenshots vernieuwen

Plaatjes staan in `docs/gebruiker/screenshots/`. Werk ze bij een **getagde release** bij en pas de versieregels in `HANDLEIDING.md` aan.

### Optie A — echte UI (aanbevolen op ontwikkel-PC met display)

```powershell
pip install -e .[dev]
python scripts/capture_gebruikershandleiding_screenshots.py
```

Vereist PySide6 en een werkende Qt-GUI (geen headless-crash).

### Optie B — schematische mock (labels uit `messages.py`)

Als Qt-grabs niet lukken (CI/headless), of als tussenoplossing vóór release:

```powershell
pip install Pillow
python scripts/generate_gebruikershandleiding_screenshots_mock.py
```

De mock gebruikt **juiste Nederlandse UI-labels** maar geen live pixels van de app — vervang bij release door optie A waar mogelijk.

## PDF-export (optioneel lokaal)

Pandoc-voorbeeld (indien geïnstalleerd):

```powershell
pandoc docs/gebruiker/HANDLEIDING.md -o docs/gebruiker/RCM2-gebruikershandleiding.pdf --resource-path=docs/gebruiker
```

Of gebruik de Claude-prompt in `PROMPT_OPMAAK.md` voor een opgemaakt Word/PDF-document.
