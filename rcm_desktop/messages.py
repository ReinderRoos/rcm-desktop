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
FM_RESULTS_GROUP_TITLE = "Faalwijzen-resultaten"
FM_RESULTS_HEADER_FM_ID = "FM-id"
FM_RESULTS_HEADER_FAALWIJZE = "Faalwijze"
FM_RESULTS_HEADER_PBS_ID = "PBS-id"
FM_RESULTS_HEADER_BOUWDEEL_NAAM = "Bouwdeel"
FM_RESULTS_HEADER_FAALMOMENTEN = "Faalmomenten lifecycle"
FM_RESULTS_HEADER_DOWNTIME_HR = "Downtime (uur)"
FM_RESULTS_HEADER_TOTAL_COST_EUR = "Totale kosten (EUR)"
PBS_RESULTS_GROUP_TITLE = "PBS-resultaten"
PBS_RESULTS_HEADER_PBS_ID = "PBS-id"
PBS_RESULTS_HEADER_BOUWDEEL = "Bouwdeel"
PBS_RESULTS_HEADER_LEVEL = "Niveau"
PBS_RESULTS_HEADER_FAALMOMENTEN_TOTAL = "Faalmomenten lifecycle (totaal)"
PBS_RESULTS_HEADER_DOWNTIME_TOTAL_HR = "Downtime (uur, totaal)"
PBS_RESULTS_HEADER_UNAVAILABILITY_TOTAL = "Niet-beschikbaarheid (%, totaal)"
PBS_RESULTS_HEADER_COST_TOTAL_EUR = "Totale kosten (EUR, totaal)"
FAALWIJZEN_EDIT_GROUP_TITLE = "Faalwijzen bewerken"
FAALWIJZEN_EDIT_HEADER_FM_ID = "FM-id"
FAALWIJZEN_EDIT_HEADER_PBS_ID = "PBS-id"
FAALWIJZEN_EDIT_HEADER_OMSCHRIJVING = "Faalwijze (omschrijving)"
FAALWIJZEN_EDIT_HEADER_FUNCTIE = "Functie-id"
FAALWIJZEN_EDIT_HEADER_MTTF = "MTTF (jaar)"
FAALWIJZEN_EDIT_HEADER_SIGMA = "Sigma (jaar)"
FAALWIJZEN_EDIT_HEADER_COST_CM = "CM-kosten (EUR)"
FAALWIJZEN_EDIT_HEADER_P_EVENT = "P (ongewenste gebeurtenis)"


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, "Onbekende status")
