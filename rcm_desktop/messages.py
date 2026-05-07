from __future__ import annotations

STATUS_LABELS = {
    "idle": "Nog niet gevalideerd.",
    "busy": "Valideren...",
    "valid": "Geldig",
    "valid_with_warnings": "Geldig met waarschuwingen",
    "invalid": "Ongeldig",
    "error": "Fout",
}

ERROR_DIALOG_TITLE = "Validatie mislukt"
RUN_ERROR_DIALOG_TITLE = "Analyse-run mislukt"
ERROR_EMPTY_PATH = "Kies eerst een projectbestand (*.rcm.json of *.json)."
ERROR_DEFAULT_FIXTURE_MISSING = "Geen standaard fixture gevonden. Kies handmatig een bestand."
PREVIEW_GROUP_TITLE = "Projectoverzicht"
PREVIEW_LABEL_PBS = "Aantal PBS-items:"
PREVIEW_LABEL_FUNCTIES = "Aantal functies:"
PREVIEW_LABEL_FAALWIJZES = "Aantal faalwijzen:"
PREVIEW_LABEL_PM_TASKS = "Aantal PM-taken:"
PREVIEW_TOP5_TITLE = "Top 5 faalwijzen"
PREVIEW_EMPTY_TOP5 = "(geen faalwijzen)"
RUN_GROUP_TITLE = "Analyseresultaat"
RUN_LABEL_STATUS = "Status:"
RUN_LABEL_SUMMARY = "Samenvatting:"
RUN_LABEL_FM_RESULTS = "#FM-results:"
RUN_LABEL_TOTAL_FAALMOMENTEN = "Totale faalmomenten lifecycle:"
RUN_LABEL_TOTAL_COST_EUR = "Totale kosten (EUR):"


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, "Onbekende status")
