from __future__ import annotations

STATUS_LABELS = {
    "idle": "Nog niet gevalideerd.",
    "valid": "Geldig",
    "valid_with_warnings": "Geldig met waarschuwingen",
    "invalid": "Ongeldig",
    "error": "Fout",
}

STATUS_BUSY_LOADING = "Bezig met laden…"
STATUS_BUSY_RUNNING = "Bezig met analyseren…"

PICK_BUTTON_LABEL = "Kies bestand"
VALIDATE_BUTTON_LABEL = "Project inladen"
VALIDATE_BUTTON_TOOLTIP = (
    "Leest het gekozen projectbestand in en valideert het domain model (structuur en verwijzingen). "
    "Daarna kunt u Faalwijzen aanpassen, een volledige lifecycle-analyse draaien en what-if planning in LCC verkennen. "
    "Tip: eerst dit uitvoeren tot het project geldig is."
)
RUN_BUTTON_TOOLTIP = (
    "Voert één volledige lifecycle-analyse uit op het ingeladen project "
    "(eventueel inclusief uw faalwijzen-wijzigingen). Vult de FM-resultatentabel en PBS-resultatenboom. "
    "Werkt na een geldig ingeladen project. In de resultatenwerkruimte: met What-if planning actief "
    "worden passieve taken in de run meegenomen."
)
COMPARE_BUTTON_TOOLTIP = (
    "Draait twee berekeningen naast elkaar: een CM-scenario (minimaal preventief: SVO en wettelijke taken) "
    "en een PM-scenario (volledige preventieve taken), en toont KPI-vergelijkingen "
    "(faalmomenten, kosten, niet-beschikbaarheid). Dit is geen vervanging van de volledige analyse-tabellen, "
    "maar een gerichte CM/PM-vergelijking. Werkt na een geldig ingeladen project; u hoeft niet eerst "
    "\"Volledige analyse\" te draaien."
)
ERROR_DIALOG_TITLE = "Validatie mislukt"
RUN_ERROR_DIALOG_TITLE = "Analyse-run mislukt"
COMPARE_ERROR_DIALOG_TITLE = "Scenariovergelijking mislukt"
SAVE_ERROR_DIALOG_TITLE = "Opslaan mislukt"
UNSAVED_DIALOG_TITLE = "Niet-opgeslagen wijzigingen"
ERROR_EMPTY_PATH = "Kies eerst een projectbestand (*.rcm.json of *.json)."
ERROR_DEFAULT_FIXTURE_MISSING = "Geen standaard fixture gevonden. Kies handmatig een bestand."
OVERVIEW_STRIP_GROUP_TITLE = "Projectoverzicht & analyse"
PREVIEW_LABEL_PBS = "Aantal PBS-items:"
PREVIEW_LABEL_FUNCTIES = "Aantal functies:"
PREVIEW_LABEL_FAALWIJZES = "Aantal faalwijzen:"
PREVIEW_LABEL_PM_TASKS = "Aantal PM-taken:"
PREVIEW_TOP5_TITLE = "Top 5 faalwijzen"
PREVIEW_EMPTY_TOP5 = "(geen faalwijzen)"
RUN_LABEL_STATUS = "Status:"
RUN_LABEL_SUMMARY = "Samenvatting:"
RUN_LABEL_FM_RESULTS = "#FM-results:"
RUN_LABEL_TOTAL_FAALMOMENTEN = "Totale faalmomenten lifecycle:"
RUN_LABEL_TOTAL_COST_EUR = "Totale kosten (EUR):"
RUN_BUTTON_LABEL = "Volledige analyse"
COMPARE_BUTTON_LABEL = "Vergelijk scenario's (CM/PM)"
COMPARE_GROUP_TITLE = "Scenariovergelijking (CM vs PM)"
LCC_RUN_GROUP_TITLE = "LCC — huidig project (één volledige analyse)"
LCC_RUN_GROUP_TOOLTIP = (
    "Verwachte nominale EUR per kalenderjaar (kalenderjaar = modeljaar + horizonindex). "
    "Correctief: faalgebonden kosten (kosten per faalgebeurtenis × verwachte faalmomenten), over jaren verdeeld. "
    "Voor verouderingsfalen komt de jaarverdeling uit dezelfde aging-motor als het totaal (meerdere faalmomenten "
    "en reparatiekwaliteit inbegrepen; Φ-segmenten per jaar); voor willekeurige falen blijft de intensiteit "
    "per jaar modelconsistent (vaak vlak). "
    "Het totaal correctief blijft gelijk aan de motor. "
    "Preventief: kosten van PM-taken (LTAP-/motorconsistent), over jaren verdeeld. "
    "Geen tweede scenario — dit is de laatste geslaagde volledige analyse op het actuele project. "
    "Geen contante waarde/discontering."
)
LCC_RUN_HINT = (
    "Verwachte nominale kosten per kalenderjaar voor het huidige project (één run). "
    "Correctief en preventief zijn beide zichtbaar; dit is niet hetzelfde als een CM/PM-scenariovergelijking."
)
LCC_COMPARE_TABLE_TITLE = "LCC — scenariovergelijking per kalenderjaar"
LCC_COMPARE_CHART_TITLE = "LCC — scenario's per kalenderjaar (correctief + preventief)"
LCC_HEADER_CALENDAR_YEAR = "Kalenderjaar"
LCC_HEADER_CORRECTIEF_EUR = "Correctief (EUR)"
LCC_HEADER_PREVENTIEF_EUR = "Preventief (EUR)"
LCC_HEADER_TOTAL_EUR = "Totaal (EUR)"
LCC_HEADER_CM_SCENARIO_CORRECTIEF = "CM — correctief (EUR)"
LCC_HEADER_CM_SCENARIO_PREVENTIEF = "CM — preventief (EUR)"
LCC_HEADER_PM_SCENARIO_CORRECTIEF = "PM — correctief (EUR)"
LCC_HEADER_PM_SCENARIO_PREVENTIEF = "PM — preventief (EUR)"
LCC_TOOLTIP_HEADER_CORRECTIEF = (
    "Correctief (faalgebonden): verwachte kosten verdeeld over kalenderjaren naar verwachte faalmomenten. "
    "Voor veroudering: jaarspreiding is motorconsistent (zelfde aging-iteratie als het totaal; Φ-segmenten). "
    "REV-taken verlagen de effectieve leeftijd op geplande interval-momenten (aging_effect_pct). "
    "Niet hetzelfde als het CM-scenario; correctief komt ook voor in het PM-scenario."
)
LCC_TOOLTIP_HEADER_PREVENTIEF = (
    "Preventief: kosten van geplande PM-taken (inclusief taakgroepen) verdeeld over kalenderjaren, "
    "aansluitend op LTAP-planning."
)
LCC_TOOLTIP_HEADER_CM_SCENARIO_CORRECTIEF = (
    "CM-scenario: correctief (faalgebonden) voor de run op het CM-project (min PM behalve SVO/wettelijk). "
    "Jaarspreiding: aging is motorconsistent (aging-SSOT); random blijft modelconsistent."
)
LCC_TOOLTIP_HEADER_CM_SCENARIO_PREVENTIEF = (
    "CM-scenario: preventief (PM-taken) voor de run op het CM-project (alleen resterende PM, o.a. SVO/wettelijk)."
)
LCC_TOOLTIP_HEADER_PM_SCENARIO_CORRECTIEF = (
    "PM-scenario: correctief (faalgebonden) voor de run op het volledige-PM-project. "
    "Jaarspreiding: aging is motorconsistent (aging-SSOT); random blijft modelconsistent."
)
LCC_TOOLTIP_HEADER_PM_SCENARIO_PREVENTIEF = (
    "PM-scenario: preventief (PM-taken) voor de run op het volledige-PM-project."
)
LCC_CHART_SET_CORRECTIEF = "Correctief"
LCC_CHART_SET_PREVENTIEF = "Preventief"
LCC_CHART_SET_CM_CORRECTIEF = "CM — correctief"
LCC_CHART_SET_CM_PREVENTIEF = "CM — preventief"
LCC_CHART_SET_PM_CORRECTIEF = "PM — correctief"
LCC_CHART_SET_PM_PREVENTIEF = "PM — preventief"
LCC_CELL_TOOLTIP_CORRECTIEF_PREVENTIEF = "Correctief: {c} | Preventief: {p}"
LCC_CHART_SCROLL_TOOLTIP = (
    "Horizontaal scrollen bij veel kalenderjaren: de grafiek is breder dan het venster "
    "zodat categorieën leesbaar blijven."
)
PANEL_TOGGLE_PREVIEW = "Overzicht"
PANEL_TOGGLE_FAALWIJZEN = "Faalwijzen"
PANEL_TOGGLE_COMPARE = "Vergelijking"
PANEL_RESET_LAYOUT_BUTTON = "Herstel vensterindeling"
TABLE_WORD_WRAP_TOGGLE_LABEL = "Tekstomloop"
TABLE_WORD_WRAP_TOGGLE_TOOLTIP = (
    "Schakel tekstomloop in tabellen (Faalwijzen, FM-resultaten, LTAP-detail) aan of uit. "
    "Aan: lange teksten breken over meerdere regels. Uit: compacte enkele regels. "
    "Uw keuze wordt onthouden."
)
RESULT_FOCUS_FM_BUTTON = "FM-resultaten"
RESULT_FOCUS_PBS_BUTTON = "PBS-resultaten"
LTAP_GROUP_TITLE = "LTAP PM-planning (what-if)"
LTAP_GROUP_TOOLTIP = (
    "Horizon en jaarschalen gebruiken het kalenderjaar = modeljaar + horizonindex uit de projectconfig. "
    "Modeljaar is de peildatum voor lifecycle/PBS-leeftijd — niet het bouwjaar van een onderdeel."
)
LTAP_SELECT_LABEL = "Geselecteerde PM-taken:"
LTAP_SHIFT_LABEL = "Shift (jaar):"
LTAP_SHIFT_SPIN_TOOLTIP = (
    "Verschuiving in horizonjaren (dezelfde index als de LTAP-buckets). Kalenderjaar = modeljaar + horizonindex."
)
LTAP_APPLY_BUTTON = "Bundel toepassen"
LTAP_RESET_BUTTON = "Herstel LTAP-baseline"
LTAP_FILTER_REV_ONLY_BUTTON = "Toon alleen REV"
LTAP_FILTER_SHOW_ALL_BUTTON = "Toon alle taken"
LTAP_ERROR_DIALOG_TITLE = "LTAP-bundeling mislukt"
LTAP_SELECTION_REQUIRED_ERROR = "Selecteer minimaal 1 zichtbare PM-taak in de LTAP-tabel."
LTAP_IMPACT_LABEL_EMPTY = "Nog geen LTAP-bundelimpact."
LTAP_CONTEXT_LABEL = "Context: {filter_mode} | {year_mode} | {selection_mode} | {overlay_mode}"
LTAP_CONTEXT_FILTER_ALL = "filter alle taken"
LTAP_CONTEXT_FILTER_REV = "filter REV"
LTAP_CONTEXT_YEAR_ALL = "alle jaren"
LTAP_CONTEXT_YEAR_SELECTED = "kalenderjaar {calendar_year}"
LTAP_CONTEXT_SELECTION_EMPTY = "geen selectie"
LTAP_CONTEXT_SELECTION_COUNT = "{count} geselecteerd"
LTAP_CONTEXT_OVERLAY_INACTIVE = "baseline actief"
LTAP_CONTEXT_OVERLAY_ACTIVE = "what-if actief ({count})"
LTAP_CHART_HINT_LABEL = "Kostenverloop per kalenderjaar (klik op een jaar voor detailtabel):"
LTAP_CHART_TITLE = "LTAP onderhoudskosten per kalenderjaar"
LTAP_MODELJAAR_PEILDATUM_TOOLTIP = (
    "Jaartallen zijn kalenderjaren: modeljaar (uit config) + horizonindex. "
    "Modeljaar is de referentie voor horizon en PBS-leeftijd, niet het bouwjaar van een onderdeel."
)
LTAP_CHART_SERIES_BASELINE = "Baseline"
LTAP_CHART_SERIES_WHAT_IF = "What-if"
LTAP_CHART_AXIS_Y_TITLE = "Kosten (EUR)"
LTAP_SHOW_ALL_YEARS_BUTTON = "Toon alle jaren"
LTAP_YEAR_SUMMARY_EMPTY = "Geen jaar geselecteerd."
LTAP_YEAR_SUMMARY_LABEL = "Jaar {calendar_year}: baseline {baseline} | what-if {what_if} | Δ {delta}"
LTAP_DETAIL_EMPTY_TEXT = "Geen werkzaamheden in dit jaar."
LTAP_DETAIL_HEADER_PM_ID = "PM-id"
LTAP_DETAIL_HEADER_PM_TOOLTIP = (
    "Compact label: PM_<TYPE>_[WET_]_[TG_]_NN (TYPE=SVO/IN/TST/REV; WET/TG alleen indien van toepassing; "
    "NN is globaal volgnummer over alle PM-taken). Hover op een cel voor het canonieke project-ID."
)
LTAP_SELECT_INPUT_TOOLTIP = (
    "Selectie gebruikt het canonieke PM-project-ID (JSON-sleutel). Zichtbare voorvoegsels volgen het LTAP-labelcontract."
)
LTAP_PM_CELL_TOOLTIP = "Canonieke project-ID (JSON): {pm_id}"
LTAP_DETAIL_HEADER_FAALWIJZ = "Faalwijze"
LTAP_DETAIL_HEADER_FAALWIJZ_TOOLTIP = (
    "Deze kolom toont de faalwijze-omschrijving uit het domain model. "
    "Het canonieke Faalwijze-ID (JSON-sleutel) staat op de cel-tooltip, vergelijkbaar met PM-id op de eerste kolom."
)
LTAP_DETAIL_HEADER_TASK = "Werkzaamheid"
LTAP_DETAIL_HEADER_EXECUTIONS = "Uitv."
LTAP_DETAIL_HEADER_COST_EUR = "Kosten (EUR)"
LTAP_DETAIL_HEADER_COST_TOOLTIP = (
    "Kosten per rij (uitvoeringen × tarief). €0 lichtgrijs: verwacht "
    "(taakgroep-kosten op groepsniveau in de motor, of expliciete aanname). €0 oranje/vet: "
    "waarschuwing — controleer invoer."
)
LTAP_DETAIL_HEADER_DOWNTIME_HR = "Downtime (uur)"
LTAP_DETAIL_NON_SHIFTABLE_TAG = "niet-verschuifbaar"
FM_RESULTS_GROUP_TITLE = "Faalwijzen-resultaten"
FM_RESULTS_HEADER_FM_ID = "FM-id"
FM_RESULTS_HEADER_BOUWDEEL_NAAM = "Bouwdeel"
FM_RESULTS_HEADER_FAALWIJZE = "Faalwijze"
FM_RESULTS_HEADER_NMF = "NMF"
FM_RESULTS_HEADER_RF = "RF"
FM_RESULTS_NMF_YES = "NMF"
FM_RESULTS_FILTER_BOUWDEEL = "Filter bouwdeel"
FM_RESULTS_FILTER_PLACEHOLDER = "Deel van bouwdeelnaam…"
TABLE_FILTER_TEXT_PLACEHOLDER = "Filter…"
TABLE_FILTER_NUMERIC_PLACEHOLDER = ">100, 10..50"
TABLE_FILTER_BOOL_ALL = "Alle"
TABLE_FILTER_CLEAR = "Wis filters"
TABLE_FILTER_ROW_COUNT = "{visible} / {total} rijen"
TABLE_FILTER_INVALID_TOOLTIP = "Ongeldige expressie — alle rijen worden getoond"
FM_RESULTS_HEADER_PBS_ID = "PBS-id"
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
FAALWIJZEN_EDIT_HEADER_FAILURE_TYPE = "Faaltype"
FAALWIJZEN_EDIT_HEADER_NMF = "NMF"
FAALWIJZEN_EDIT_HEADER_REPAIR_QUALITY = "Repair quality"
FAALWIJZEN_FAILURE_RANDOM = "Exponentieel (random)"
FAALWIJZEN_FAILURE_AGING = "Veroudering (aging)"
FAALWIJZEN_NMF_JA = "Ja"
FAALWIJZEN_NMF_NEE = "Nee"
FAALWIJZEN_FILTER_FAILURE_TYPE = "Faaltype"
FAALWIJZEN_FILTER_NMF = "NMF"
FAALWIJZEN_FILTER_ALL = "Alle"
FAALWIJZEN_SEARCH_PLACEHOLDER = "Zoek op FM-id of omschrijving…"
FAALWIJZEN_BULK_APPLY_SELECTION = "Pas toe op selectie…"
FAALWIJZEN_BULK_APPLY_VISIBLE = "Pas toe op zichtbare rijen…"
FAALWIJZEN_BULK_DIALOG_TITLE = "Bulk-wijziging"
FAALWIJZEN_BULK_FIELD_LABEL = "Veld"
FAALWIJZEN_BULK_VALUE_LABEL = "Nieuwe waarde"
FAALWIJZEN_BULK_FAILED = "Bulk-wijziging mislukt:\n{detail}"
FAALWIJZEN_BULK_LARGE_WARNING = (
    "Je past deze wijziging toe op {count} rijen. Doorgaan?"
)
FAALWIJZEN_EDIT_HEADER_OMSCHRIJVING = "Faalwijze (omschrijving)"
FAALWIJZEN_EDIT_HEADER_FUNCTIE = "Functie-id"
FAALWIJZEN_EDIT_HEADER_MTTF = "MTTF (jaar)"
FAALWIJZEN_EDIT_HEADER_SIGMA = "Sigma (jaar)"
FAALWIJZEN_EDIT_HEADER_AGING_DISTRIBUTION = "Aging-verdeling"
FAALWIJZEN_EDIT_HEADER_BETA = "Beta (jaar)"
FAALWIJZEN_EDIT_HEADER_COST_CM = "CM-kosten (EUR)"
FAALWIJZEN_EDIT_HEADER_P_EVENT = "P (ongewenste gebeurtenis)"
WORKSPACE_WINDOW_TITLE = "RCM2 desktop — resultatenwerkruimte"
WORKSPACE_MENU_FILE = "Bestand"
WORKSPACE_MENU_VIEW = "Beeld"
WORKSPACE_MENU_RUN = "Run"
WORKSPACE_MENU_ANALYSIS = "Analyse"
WORKSPACE_MENU_TOGGLE_WHATIF = "What-if planning"
WORKSPACE_MENU_RUN_SLOT_A = "Run → A"
WORKSPACE_MENU_RUN_SLOT_B = "Run → B"
WORKSPACE_MENU_COMPARE_SCENARIO_CM = "Scenario CM"
WORKSPACE_MENU_COMPARE_SCENARIO_PM = "Scenario PM"
WORKSPACE_MENU_OPEN_PROJECT = "Project inladen…"
WORKSPACE_MENU_OPEN_RCM_COST = "Open RCM-Cost export…"
WORKSPACE_MENU_QUIT = "Afsluiten"
WORKSPACE_MENU_PBS_TREE_VISIBLE = "PBS-boom zichtbaar"
WORKSPACE_MENU_PBS_SELECT_PREV_SIBLING = "Vorige PBS op niveau"
WORKSPACE_MENU_PBS_SELECT_NEXT_SIBLING = "Volgende PBS op niveau"
WORKSPACE_MENU_PBS_SELECT_PARENT = "Naar parent PBS"
WORKSPACE_MENU_PBS_SELECT_FIRST_CHILD = "Naar eerste kind"
WORKSPACE_MENU_PBS_MOVE_UP = "PBS omhoog verplaatsen"
WORKSPACE_MENU_PBS_MOVE_DOWN = "PBS omlaag verplaatsen"
WORKSPACE_MENU_KPI_OVERVIEW = "KPI-overzicht"
WORKSPACE_MENU_FAALWIJZEN_GRID = "Faalwijzen-grid…"
WORKSPACE_PBS_SIDEBAR_TITLE = "Componenten"
WORKSPACE_PBS_TOGGLE_LABEL = "Component-kolom"
WORKSPACE_PBS_TOGGLE_TOOLTIP = (
    "Toon of verberg de component-kolom links. Standaard zichtbaar; "
    "verbergen geeft meer ruimte voor grafiek en tabel."
)
WORKSPACE_PBS_FILTER_PLACEHOLDER = "Filter op component-id of bouwdeel…"
WORKSPACE_PBS_FILTER_TOOLTIP = (
    "Substring-filter op component-id en bouwdeelnaam. Gematchte paden klappen automatisch uit; "
    "leeg laten toont de hele structuur ingeklapt."
)
WORKSPACE_PBS_EMPTY_STATE = "Geen componenten die overeenkomen met dit filter."
WORKSPACE_SHOW_WHOLE_PROJECT_BUTTON = "Toon hele project"
WORKSPACE_SHOW_WHOLE_PROJECT_TOOLTIP = (
    "Herstel scope naar het volledige project — alle PBS-onderdelen zichtbaar in de detailtabel."
)
WORKSPACE_DETAIL_EMPTY_STATE = (
    "Nog geen analyseresultaten. Start een analyse; daarna kunt u in LCC what-if planning verkennen."
)
WORKSPACE_KPI_PLACEHOLDER = "Hier komt later de KPI-tabel."

# Modus-segmented control (slice 23, fase B) + sub-toggles en metric-labels.
WORKSPACE_MODE_BIJDRAGEN = "Top 10"
WORKSPACE_MODE_LCC = "LCC-plot"
WORKSPACE_MODE_FM_DETAIL = "FM-resultaten"

# View-registry (slice 79) — gebruikerslabels voor Input/Output-navigatie.
WORKSPACE_SIDE_INPUT = "Input"
WORKSPACE_SIDE_OUTPUT = "Output"
WORKSPACE_VIEW_TOP_10 = "Top 10"
WORKSPACE_VIEW_LCC_PLOT = "LCC-plot"
WORKSPACE_VIEW_LTAP = "LTAP"
WORKSPACE_VIEW_FM_RESULTS = "FM-resultaten"
WORKSPACE_VIEW_FAALWIJZEN = "Faalwijzen"
WORKSPACE_VIEW_REV_TASKS = "REV-taken"
WORKSPACE_VIEW_EFFECTEN = "Effecten"
WORKSPACE_VIEW_TAAKGROEPEN = "Taakgroepen"
WORKSPACE_VIEW_CORRECTIEF = "Correctief onderhoud"
WORKSPACE_ENTITY_GRID_COLUMNS = "Kolommen"
ENTITY_GRID_COLUMNS_DIALOG_TITLE = "Kolommen kiezen"
ENTITY_GRID_SEARCH_PLACEHOLDER = "Zoeken in tabel…"
ENTITY_GRID_ROW_COUNT = "{visible} van {total} rijen"
ENTITY_GRID_FINDINGS_SUFFIX = " · {errors} fouten, {warnings} waarschuwingen"
WORKSPACE_MENU_REVALIDATE_INPUT = "Controleer invoer"
ENTITY_GRID_SCOPE_NOT_APPLICABLE = "PBS-scope niet van toepassing — toont alle {entity}"
ENTITY_GRID_PM_FIRST_EXECUTION_YEAR = "Eerste jaar uitvoering"
ENTITY_GRID_PM_EXECUTION_COUNT_LCC = "Aantal uitvoeringen in LCC-periode"
ENTITY_GRID_PM_DOWNTIME_OH = "Downtime bij OH"
ENTITY_GRID_PM_REPAIR_QUALITY = "Repair quality"
ENTITY_GRID_PM_HERSTELDUUR = "Herstelduur"
WORKSPACE_INPUT_PLACEHOLDER = (
    "Invoertabellen (faalwijzen, taken, effecten) volgen in een latere slice."
)

WORKSPACE_TOP10_SUBBAR_LABEL = "Top 10:"
WORKSPACE_SOURCE_TOGGLE_PBS = "Component"
WORKSPACE_SOURCE_TOGGLE_FAALWIJZE = "Faalwijze"
WORKSPACE_SOURCE_TOGGLE_EFFECTKLASSE = "Effectklasse"

WORKSPACE_METRIC_NIET_BESCHIKBAARHEID = "Niet-beschikbaarheid"
WORKSPACE_METRIC_KOSTEN = "Kosten"
WORKSPACE_NB_EFFECT_FILTER_LABEL = "NB-effecten"
WORKSPACE_NB_EFFECT_FILTER_DISABLED_REASON = (
    "Geen bijdrage in kosten, faalmomenten of downtime voor de totale PBS"
)
WORKSPACE_NB_EFFECT_FILTER_TOOLTIP = (
    "Filter op niet-beschikbaarheidseffecten. Geen selectie = totale NB."
)
WORKSPACE_METRIC_FAALMOMENTEN = "Faalmomenten"
WORKSPACE_METRIC_EFFECTIMPACT = "Effectimpact"

WORKSPACE_CONTRIBUTION_HORIZON_LIFECYCLE = "Per LCC-periode"
WORKSPACE_CONTRIBUTION_HORIZON_PER_YEAR = "Per jaar"
WORKSPACE_CONTRIBUTION_YEAR_AVERAGE = "Ø per jaar"
WORKSPACE_CONTRIBUTION_NB_HOURS = "Uren"
WORKSPACE_CONTRIBUTION_NB_PERCENT = "%"

WORKSPACE_CONTRIBUTION_HORIZON_TOOLTIP = (
    "Per LCC-periode: lifecycle-totaal. Per jaar: gemiddelde per horizonbucket "
    "of één geselecteerd kalenderjaar."
)
WORKSPACE_CONTRIBUTION_YEAR_AVERAGE_TOOLTIP = (
    "Gemiddelde waarde per horizonbucket over de lifecycle."
)
WORKSPACE_CONTRIBUTION_NB_PERCENT_TOOLTIP = (
    "Percentage t.o.v. 8760 uur per kalenderjaar (24/7)."
)

WORKSPACE_BIJDRAGE_HEADER_CATEGORIE = "Categorie"
WORKSPACE_BIJDRAGE_HEADER_WAARDE = "Waarde"
WORKSPACE_BIJDRAGE_HEADER_AANDEEL = "Aandeel %"

WORKSPACE_BIJDRAGE_EMPTY_STATE = (
    "Geen bijdragers in de huidige scope. Pas scope of bron aan."
)

# LCC-modus (slice 23, fase C — issue 03).
WORKSPACE_LCC_TABLE_HEADER_KALENDERJAAR = "Kalenderjaar"
WORKSPACE_LCC_TABLE_HEADER_CORRECTIEF = "Correctief (EUR)"
WORKSPACE_LCC_TABLE_HEADER_PREVENTIEF = "Preventief (EUR)"
WORKSPACE_LCC_TABLE_HEADER_TOTAAL = "Totaal (EUR)"
WORKSPACE_LCC_EMPTY_STATE = (
    "Nog geen LCC-kosten. Start eerst een analyse-run en kies daarna `LCC`."
)
LCC_PLOT_AXIS_X_KALENDERJAREN = "Kalenderjaren"
LCC_PLOT_AXIS_Y_FAALMOMENTEN = "Aantal keer falen"
LCC_PLOT_AXIS_Y_NB_HOURS = "Niet-beschikbaarheid (uren)"
LCC_PLOT_AXIS_Y_NB_PERCENT = "Niet-beschikbaarheid (%)"
LCC_PLOT_AXIS_Y_KOSTEN = "Kosten (EUR)"
WORKSPACE_LCC_MODE_TOOLTIP = (
    "LCC toont kosten per kalenderjaar (correctief + preventief) voor de huidige "
    "analyse-run. De LCC-weergave is project-totaal en wordt niet beperkt door de "
    "PBS-scope; scoped LCC volgt in een latere slice."
)

# Niet-beschikbaarheid-modus (slice 23, fase D — issue 04).
WORKSPACE_UNAVAILABILITY_TABLE_HEADER_KALENDERJAAR = "Kalenderjaar"
WORKSPACE_UNAVAILABILITY_TABLE_HEADER_PCT = "Niet-beschikbaarheid %"
WORKSPACE_UNAVAILABILITY_TABLE_HEADER_DOWNTIME = "Downtime (uur)"
WORKSPACE_UNAVAILABILITY_CHART_TITLE = (
    "Niet-beschikbaarheid per kalenderjaar — motor-horizonprofiel"
)
WORKSPACE_UNAVAILABILITY_PROXY_DISCLAIMER = (
    "Jaarverdeling uit het motor-horizonprofiel (correctieve downtime + verborgen "
    "niet-beschikbaarheid). Lifecycle-totalen reconciliëren met de motor."
)
WORKSPACE_HORIZON_PROFILE_LEGACY_DISCLAIMER = (
    "Oude cache zonder jaarprofiel: tijdelijke proxy-verdeling actief. Voer een "
    "volledige herberekening uit voor jaarcijfers uit de motor."
)
WORKSPACE_UNAVAILABILITY_EMPTY_STATE = (
    "Nog geen niet-beschikbaarheidsdata. Start eerst een analyse-run en kies "
    "daarna `Niet-beschikbaarheid`."
)

# Preventief-onderhoud-modus (slice 23, fase D — issue 05).
WORKSPACE_PM_SUBMODE_KOSTEN = "Kosten"
WORKSPACE_PM_SUBMODE_AANTAL_UITVOERINGEN = "Aantal uitvoeringen"
WORKSPACE_PM_TABLE_HEADER_KALENDERJAAR = "Kalenderjaar"
WORKSPACE_PM_TABLE_HEADER_WAARDE_KOSTEN = "Kosten (EUR)"
WORKSPACE_PM_TABLE_HEADER_WAARDE_AANTAL = "Aantal uitvoeringen"
WORKSPACE_PM_TABLE_HEADER_CUMULATIEF_KOSTEN = "Cumulatief (EUR)"
WORKSPACE_PM_TABLE_HEADER_CUMULATIEF_AANTAL = "Cumulatief aantal"
WORKSPACE_PM_EMPTY_STATE = (
    "Nog geen PM-werk. Start eerst een analyse-run en kies daarna "
    "`Preventief onderhoud`."
)
WORKSPACE_PM_WHATIF_HINT = (
    "Kosten: what-if-preview · Aantal uitvoeringen: laatste analyse (baseline)"
)
WORKSPACE_PM_MODE_TOOLTIP = (
    "PM-werk per kalenderjaar — read-only weergave. Toggle tussen kosten en "
    "aantal uitvoeringen; bewerken van het LTAP-onderhoudsschema gebeurt in de "
    "LTAP-tab."
)

# Analyse-run en KPI-tabel (slice 26).
WORKSPACE_START_ANALYSE_BUTTON_LABEL = "Start analyse"
WORKSPACE_RECOMPUTE_ANALYSE_BUTTON_LABEL = "Herbereken analyse"
WORKSPACE_START_ANALYSE_BUTTON_TOOLTIP = (
    "Voer de volledige lifecycle-analyse uit op het geladen project. "
    "Met What-if planning actief worden passieve taken in de motor-run meegenomen; "
    "in LCC kunt u daarna presets (bijv. CM-beleid) en verschuivingen verkennen zonder "
    "aparte CM/PM-scenario-runs."
)
WORKSPACE_RUN_PHASE_MOTOR = "Motor…"
WORKSPACE_RUN_PHASE_PRESENTATION = "Presentatie…"
WORKSPACE_RUN_PHASE_PRESENTATION_UPDATE = "Presentatie bijwerken…"
WORKSPACE_KPI_TABLE_HEADER_KPI = "KPI"
WORKSPACE_RUN_OTHER_SCENARIO_PLACEHOLDER = (
    "Scenario-vergelijking is vervangen door what-if in LCC-modus."
)
WORKSPACE_SCENARIO_CM_TITLE = "CM-scenario"
WORKSPACE_SCENARIO_PM_TITLE = "PM-scenario"

# A/B-scenariovergelijking (slice 56).
WORKSPACE_COMPARE_SCENARIO_LABEL = "Scenario"
WORKSPACE_COMPARE_SCENARIO_PROJECT = "Project"
WORKSPACE_COMPARE_SCENARIO_CM = "CM"
WORKSPACE_COMPARE_SCENARIO_PM = "PM"
WORKSPACE_RUN_SLOT_A_BUTTON_LABEL = "Run → A"
WORKSPACE_RUN_SLOT_B_BUTTON_LABEL = "Run → B"
WORKSPACE_RUN_SLOT_A_BUTTON_TOOLTIP = (
    "Voer analyse uit en bevries resultaat in slot A (referentie)."
)
WORKSPACE_RUN_SLOT_B_BUTTON_TOOLTIP = (
    "Voer analyse uit en bevries resultaat in slot B (variant)."
)
WORKSPACE_COMPARE_TOGGLE_LABEL = "Vergelijk A ↔ B"
WORKSPACE_COMPARE_TOGGLE_TOOLTIP = (
    "Toon Top 10 en Tijdsplot naast elkaar voor gevulde slots. "
    "Slot A wordt automatisch gevuld na de eerste geslaagde analyse; "
    "gebruik Run → B voor een variant."
)
WORKSPACE_CLEAR_COMPARE_BUTTON_LABEL = "Wis vergelijking"
WORKSPACE_COMPARE_SLOT_PLACEHOLDER = "Nog geen run — gebruik Run → {slot}"
WORKSPACE_COMPARE_SLOT_HEADER = "{label}"

# Dual-project vergelijkingswerkruimte (slice 95 issue 07).
WORKSPACE_MENU_COMPARE_MODELS = "Vergelijk modellen…"
COMPARE_MODELS_WINDOW_TITLE = "Vergelijkingswerkruimte"
COMPARE_MODELS_PATH_A = "Project A (baseline)"
COMPARE_MODELS_PATH_B = "Project B (scenario)"
COMPARE_MODELS_LOAD_BUTTON = "Vergelijk"
COMPARE_MODELS_SELECT_BOTH = "Kies eerst project A en project B."
COMPARE_MODELS_SUMMARY = "{label_a} ↔ {label_b} — {count} faalwijze-regels"
COMPARE_MODELS_DETAIL_PLACEHOLDER = "Selecteer een faalwijze-regel voor invoer- en resultaatdiffs."
COMPARE_MODELS_DETAIL_TITLE = "FM {fm_a} ↔ {fm_b} ({klasse})"
COMPARE_MODELS_TABLE_HEADER_STATUS = "Status"
COMPARE_MODELS_TABLE_HEADER_FM_A = "FM A"
COMPARE_MODELS_TABLE_HEADER_FM_B = "FM B"
COMPARE_MODELS_TABLE_HEADER_CLASS = "Klasse"
COMPARE_MODELS_TABLE_HEADER_FIELD_DIFFS = "Invoer Δ"
COMPARE_MODELS_TABLE_HEADER_RESULT_DIFFS = "Resultaat Δ"
COMPARE_MODELS_DETAIL_FIELD_HEADER = ("Veld", "A", "B")
COMPARE_MODELS_DETAIL_RESULT_HEADER = ("Metric", "A", "B")

# Monte Carlo presentatie (slice 95 issue 12).
SIMULATION_RUN_MODE_LABEL = "Run-modus"
SIMULATION_RUN_MODE_ANALYTICAL = "Analytisch"
SIMULATION_RUN_MODE_MONTE_CARLO = "Monte Carlo"

# Faalwijze verwijderen (slice 99 issue 13).
FM_DELETE_BUTTON_LABEL = "Verwijder faalwijze"
FM_DELETE_BUTTON_TOOLTIP = "Verwijder de geselecteerde faalwijze uit het project"
FM_DELETE_CONFIRM_TITLE = "Faalwijze verwijderen"
FM_DELETE_CONFIRM_BODY = (
    "Faalwijze {fm_id} verwijderen?\n\n"
    "Gekoppelde entiteiten:\n"
    "• PM-taken: {pm_task_count}\n"
    "• FM-effectlinks: {fm_effect_link_count}\n"
    "• PM-effectlinks: {pm_effect_link_count}\n"
    "• Taakgroepen: {task_group_count}"
)
FM_DELETE_NO_SELECTION = "Selecteer eerst een faalwijze om te verwijderen."

# Uniformeren review (slice 95 issue 10).
NORMALIZATION_REVIEW_TITLE = "Uniformeringsvoorstellen"
NORMALIZATION_REVIEW_APPLY = "Toepassen (goedgekeurd)"
NORMALIZATION_REVIEW_ROLLBACK = "Laatste patch terugdraaien"
NORMALIZATION_REVIEW_SOURCE_A_TO_B = "A → B"
NORMALIZATION_REVIEW_SOURCE_B_TO_A = "B → A"
NORMALIZATION_REVIEW_AUDIT = "Audit trail: {count} patch(es) toegepast"
NORMALIZATION_REVIEW_NO_APPROVED = "Geen goedgekeurde voorstellen om toe te passen."
NORMALIZATION_REVIEW_TABLE_HEADERS = ("Goedkeuren", "FM A", "FM B", "Veld", "Bron", "Waarde")

# LCC-planning (slice 28).
WORKSPACE_LCC_FILTER_CM = "CM"
WORKSPACE_LCC_FILTER_REV = "REV"
WORKSPACE_LCC_FILTER_IN = "IN"
WORKSPACE_LCC_FILTER_TST = "TST"
WORKSPACE_LCC_FILTER_SVO = "SVO"
WORKSPACE_LCC_FILTER_WET = "WET"
WORKSPACE_LCC_DETAIL_HEADER_PM = "PM-taak"
WORKSPACE_LCC_DETAIL_HEADER_TYPE = "Type"
WORKSPACE_LCC_DETAIL_HEADER_FM = "Faalwijze"
WORKSPACE_LCC_DETAIL_HEADER_EXECUTIONS = "Uitvoeringen"
WORKSPACE_LCC_DETAIL_HEADER_COST = "Kosten (EUR)"
WORKSPACE_LCC_DETAIL_HEADER_DOWNTIME = "Downtime (uur)"
WORKSPACE_LCC_DETAIL_EMPTY_YEAR = "Geen taken in dit kalenderjaar voor de actieve filters."
WORKSPACE_LCC_DETAIL_CM_ONLY_LABEL = "Correctief (faalgebonden) — kalenderjaar {year}"
WORKSPACE_LCC_YEAR_SUMMARY = (
    "Jaar {year}: correctief {corr:.0f} EUR | preventief {prev:.0f} EUR"
)
WORKSPACE_LCC_YEAR_SUMMARY_WHATIF = (
    "Jaar {year}: baseline preventief {base:.0f} EUR → what-if {overlay:.0f} EUR "
    "(Δ {delta:+.0f} EUR)"
)
WORKSPACE_LCC_SHOW_ALL_YEARS = "Toon alle jaren"
WORKSPACE_LCC_WHAT_IF_TOGGLE = "What-if planning"
WORKSPACE_LCC_WHAT_IF_ACTIVE = "What-if actief ({count} wijziging(en))"
WORKSPACE_LCC_RESET_OVERLAY = "Reset naar baseline"
WORKSPACE_LCC_BULK_REV_PASSIVE = "Alle REV passief"
WORKSPACE_LCC_BULK_REV_ACTIVE = "Alle REV actief"
WORKSPACE_LCC_CM_POLICY_PRESET = "CM-beleid"
WORKSPACE_LCC_SHIFT_SELECTED = "Verschuif geselecteerd"
WORKSPACE_LCC_SHIFT_SPIN_TOOLTIP = "Aantal jaren om geselecteerde taken te verschuiven (what-if)."
WORKSPACE_LCC_DETAIL_HEADER_PASSIVE = "Passief"
WORKSPACE_LCC_SELECTION_REQUIRED = "Selecteer minstens één PM-taak in de jaardetailtabel."
WORKSPACE_LCC_CM_AFTER_RECOMPUTE = (
    "Preventief in what-if is direct zichtbaar; correctief in de analyse volgt na "
    "Herbereken analyse (what-if aan)."
)
WORKSPACE_LCC_WHAT_IF_PRESENTATION_NOTE = (
    "What-if: passief en presets wijzigen eerst de planning; zet What-if aan en "
    "herbereken om correctief in de analyse bij te werken."
)
WORKSPACE_LCC_CM_PRESET_TOOLTIP = (
    "Zet alle PM-taken passief behalve SVO, wettelijk en NMF IN/TST (zelfde als "
    "historisch CM-beleid). Geen aparte CM-scenario-run."
)
WORKSPACE_LCC_AFTER_RECOMPUTE_PASSIVE_KEPT = (
    "Analyse bijgewerkt; passieve taken blijven uit de LCC tot Reset what-if."
)
WORKSPACE_LCC_SHIFT_SELECTION_HINT = (
    "Selecteer rijen in de onderstaande tabel (niet op Passief klikken) en "
    "verschuif met de knop rechts."
)
WORKSPACE_LCC_SELECT_REV_IN_YEAR = "Selecteer REV in dit jaar"
WORKSPACE_MEEKOPPEL_PANEL_TITLE = "Meekoppelkansen"
WORKSPACE_MEEKOPPEL_PANEL_HELP = (
    "Selecteer één of meer onderdelen in de PBS-boom (Ctrl+klik voor meerdere). "
    "Alle onderliggende REV-taken worden gebundeld naar het vroegste of laatste due-jaar. "
    "De tabel toont locaties waar REV-taken binnen het tijdsvenster liggen."
)
WORKSPACE_MEEKOPPEL_WHATIF_HINT = (
    "What-if planning wordt automatisch ingeschakeld bij openen van dit paneel."
)
WORKSPACE_MEEKOPPEL_EMPTY = "Geen locatiegroepen voor het gekozen tijdsvenster."
WORKSPACE_MEEKOPPEL_EMPTY_SCOPE = "Geen meekoppelkansen in de geselecteerde boomtak."
WORKSPACE_MEEKOPPEL_WINDOW_LABEL = "Tijdsvenster (jaren):"
WORKSPACE_MEEKOPPEL_ANCHOR_EARLIER = "Bundel naar vroegste"
WORKSPACE_MEEKOPPEL_ANCHOR_LATER = "Bundel naar laatste"
WORKSPACE_MEEKOPPEL_PREVIEW = "Preview"
WORKSPACE_MEEKOPPEL_APPLY = "Toepassen"
WORKSPACE_MEEKOPPEL_SELECT_PBS = (
    "Selecteer één of meer onderdelen in de PBS-boom om REV-taken te bundelen."
)
WORKSPACE_MEEKOPPEL_SELECT_MIN_REV = (
    "Selecteer onderdelen met minstens twee REV-taken in totaal."
)
WORKSPACE_MEEKOPPEL_SELECT_MIN_SHIFTABLE_REV = (
    "In de selectie zijn minder dan twee verschuifbare REV-taken beschikbaar."
)
WORKSPACE_MEEKOPPEL_SELECTION_NONE = (
    "Selectie: geen REV-taken gevonden onder de gekozen PBS-onderdelen."
)
WORKSPACE_MEEKOPPEL_SELECTION_COUNT = (
    "Selectie bevat {count} REV-taken ({path})."
)
WORKSPACE_MEEKOPPEL_SELECT_ROW = WORKSPACE_MEEKOPPEL_SELECT_PBS
WORKSPACE_MEEKOPPEL_PREVIEW_TITLE = "Preview bundelen"
WORKSPACE_MEEKOPPEL_PREVIEW_ANCHOR_EARLIER = "Bundel naar vroegste due-jaar in de groep"
WORKSPACE_MEEKOPPEL_PREVIEW_ANCHOR_LATER = "Bundel naar laatste due-jaar in de groep"
WORKSPACE_MEEKOPPEL_PREVIEW_BODY = (
    "Locatie: {location}\n"
    "Doel: eerste uitvoering jaar {target} (≈ kalender {target_cal})\n\n"
    "{moves}\n"
    "{pbs_footnote}"
)
WORKSPACE_MEEKOPPEL_PREVIEW_PBS_FOOTNOTE = "PBS-id's: {pbs_id}"
WORKSPACE_MEEKOPPEL_PREVIEW_MOVE_LINE = (
    "  {task_label}: eerste uitvoering {from_year} → {to_year} jaar "
    "(≈ kalender {from_cal} → {to_cal}) ({shift:+d} jaar)"
)
WORKSPACE_MEEKOPPEL_PREVIEW_UNCHANGED_LINE = (
    "  {task_label}: blijft op eerste uitvoering {year} jaar (≈ kalender {cal})"
)
WORKSPACE_MEEKOPPEL_PREVIEW_SKIPPED_LINE = (
    "  {task_label}: overgeslagen ({reason})"
)
WORKSPACE_MEEKOPPEL_PREVIEW_NO_MOVES = "Alle REV-taken staan al op het doeljaar."
WORKSPACE_MEEKOPPEL_PREVIEW_BLOCKED = "Geen shift mogelijk: {reason}"
WORKSPACE_MEEKOPPEL_HEADER_PATH = "Boompad"
WORKSPACE_MEEKOPPEL_HEADER_REV_COUNT = "# REV"
WORKSPACE_MEEKOPPEL_HEADER_DUE_RANGE = "Eerste uitvoering (baseline, jaren)"
WORKSPACE_MEEKOPPEL_HEADER_SPAN = "Verschil (baseline, jaren)"
WORKSPACE_MEEKOPPEL_TOOLTIP_TASK_BASELINE = "  • {label} (baseline jaar {baseline})"
WORKSPACE_MEEKOPPEL_TOOLTIP_TASK_BASELINE_EFFECTIVE = (
    "  • {label} (baseline jaar {baseline} · effectief jaar {effective})"
)
WORKSPACE_MEEKOPPEL_PREVIEW_SCOPE_LINE = "Bundel-scope: {scope_label} ({count} REV)"
WORKSPACE_MEEKOPPEL_PREVIEW_DETERMINED_BY_ONE = (
    "Bepaald door: {label} (baseline {baseline}, effectief {effective})"
)
WORKSPACE_MEEKOPPEL_PREVIEW_DETERMINED_BY_MANY = (
    "Bepaald door: {count} taken op effectief jaar {year}"
)
WORKSPACE_MEEKOPPEL_PREVIEW_SCOPE_SWITCH_NOTICE = (
    "Scope gewijzigd: selectie is opnieuw gezet naar alle verschuifbare taken."
)
WORKSPACE_MEEKOPPEL_PREVIEW_APPLY_CONFIRM = (
    "Toepassen op {scope_label}: {count} REV-taken bundelen naar jaar {target} "
    "(kalenderjaar {target_cal})?"
)
WORKSPACE_MEEKOPPEL_PREVIEW_DIALOG_TITLE = "Preview bundelen"
WORKSPACE_MEEKOPPEL_PREVIEW_COL_SELECT = ""
WORKSPACE_MEEKOPPEL_PREVIEW_COL_TASK = "Taak"
WORKSPACE_MEEKOPPEL_PREVIEW_COL_BASELINE = "Baseline"
WORKSPACE_MEEKOPPEL_PREVIEW_COL_EFFECTIVE = "Effectief"
WORKSPACE_MEEKOPPEL_PREVIEW_COL_TARGET = "Doel"
WORKSPACE_MEEKOPPEL_PREVIEW_COL_DELTA = "Δ"
WORKSPACE_MEEKOPPEL_PREVIEW_COL_STATUS = "Status"
WORKSPACE_MEEKOPPEL_PREVIEW_SCOPE_ROW = "Locatierij"
WORKSPACE_MEEKOPPEL_PREVIEW_SCOPE_PBS = "PBS-selectie"
WORKSPACE_MEEKOPPEL_PREVIEW_SELECT_ALL_VISIBLE = "Selecteer zichtbaar"
WORKSPACE_MEEKOPPEL_PREVIEW_DESELECT_ALL_VISIBLE = "Deselecteer zichtbaar"
WORKSPACE_MEEKOPPEL_PREVIEW_FILTER_SHIFTING = "Alleen verschuivende taken"
WORKSPACE_MEEKOPPEL_PREVIEW_FILTER_ALL = "Alle taken"
WORKSPACE_MEEKOPPEL_PREVIEW_FILTER_PLACEHOLDER = "Filter op taak of PM-id…"
WORKSPACE_MEEKOPPEL_PREVIEW_SELECTION_SUMMARY = (
    "Geselecteerd: {selected} · Zichtbaar: {visible} · "
    "Verborgen geselecteerd: {hidden} · Niet selecteerbaar: {non_selectable}"
)
WORKSPACE_KPI_COLLAPSE_TOOLTIP = "KPI-paneel in- of uitklappen (alleen Tijdsplot-modus)."
WORKSPACE_LCC_WHATIF_COLLAPSE_TOOLTIP = (
    "What-if planning en LCC-filters in- of uitklappen (alleen Tijdsplot-modus)."
)
WORKSPACE_MEEKOPPEL_COLLAPSE_TOOLTIP = (
    "Meekoppelkansen-paneel in- of uitklappen (alleen Tijdsplot-modus)."
)
WORKSPACE_LCC_WHATIF_BAR_TITLE = "What-if planning & LCC-filters"
WORKSPACE_KPI_PANEL_TITLE = "KPI — huidige analyse"
WORKSPACE_PM_MODE_REDIRECT = (
    "Planning en PM-inzicht zitten nu in de LCC-modus (filters en jaardetail)."
)
WORKSPACE_FM_EVIDENT_FILTER_ALL = "Alle"
WORKSPACE_FM_EVIDENT_FILTER_NMF = "Alleen NMF"
WORKSPACE_FM_EVIDENT_FILTER_EVIDENT = "Alleen evident"
WORKSPACE_FM_COLUMN_CROP = "Bijsnijden"
WORKSPACE_FM_COLUMN_CROP_TOOLTIP = (
    "Regelomloop uit: celtekst op één regel (… + tooltip bij afkapping). "
    "Uit = tekst loopt over meerdere regels."
)

WORKSPACE_FM_INSPECTOR_EMPTY = "Selecteer een faalwijze in de tabel hierboven."
WORKSPACE_FM_INSPECTOR_TITLE = "FM-inspector"
WORKSPACE_FM_INSPECTOR_FAALMOMENTEN = "Faalmomenten (lifecycle)"
WORKSPACE_FM_INSPECTOR_RAW_DOWNTIME = "Downtime raw (uur)"
WORKSPACE_FM_INSPECTOR_DETECTION_DELAY = "Detection delay (uur)"
WORKSPACE_FM_INSPECTOR_PM_DOWNTIME = "PM-downtime (uur)"
WORKSPACE_FM_INSPECTOR_TOTAL_DOWNTIME = "Downtime totaal CM (uur)"
WORKSPACE_FM_INSPECTOR_CM_COST = "CM-kosten (EUR)"
WORKSPACE_FM_INSPECTOR_PM_COST = "PM-kosten (EUR)"
WORKSPACE_FM_INSPECTOR_TOTAL_COST = "Totale kosten (EUR)"
WORKSPACE_FM_INSPECTOR_EFFECTS = "Effectbijdragen"
WORKSPACE_FM_INSPECTOR_HASH_PREFIX = "FM-invoerhash:"
WORKSPACE_FM_INSPECTOR_HASH_MISSING = "FM-invoerhash: —"
WORKSPACE_FM_INSPECTOR_YEAR_HEADER_KALENDERJAAR = "Kalenderjaar"
WORKSPACE_FM_INSPECTOR_YEAR_HEADER_FAALMOMENTEN = "Faalmomenten"
WORKSPACE_FM_INSPECTOR_YEAR_HEADER_COR_EUR = "Correctief (EUR)"
WORKSPACE_FM_INSPECTOR_YEAR_HEADER_DOWNTIME = "Downtime (uur)"
WORKSPACE_FM_INSPECTOR_YEAR_HEADER_HIDDEN_NB = "Verborgen NB (uur)"
WORKSPACE_FM_INSPECTOR_RECONCILE_OK = "Reconcile: OK"
WORKSPACE_FM_INSPECTOR_RECONCILE_WARN = "Reconcile: waarschuwing"
WORKSPACE_FM_INSPECTOR_PROFILE_MISSING = (
    "Geen horizon_profile: alleen lifecycle-totalen zijn betrouwbaar."
)
WORKSPACE_FM_INSPECTOR_FAALMOMENTEN_PROXY_TOOLTIP = (
    "Faalmomenten per jaar zijn presentatie-proxy (zelfde pad als Top 10/LCC), "
    "geen tweede motorberekening."
)
WORKSPACE_FM_INSPECTOR_INPUTS_TITLE = "Invoer (domain model)"
WORKSPACE_FM_INSPECTOR_INITIAL_AGE = "Initiële leeftijd (jaar)"
WORKSPACE_FM_INSPECTOR_MTTF = "MTTF (jaar)"
WORKSPACE_FM_INSPECTOR_FAILURE_TYPE = "Faalmodel"
WORKSPACE_FM_INSPECTOR_FAILURE_RANDOM = "Willekeurig (random)"
WORKSPACE_FM_INSPECTOR_FAILURE_AGING = "Veroudering (aging)"
WORKSPACE_FM_INSPECTOR_SIGMA = "Standaarddeviatie (jaar)"
WORKSPACE_FM_INSPECTOR_SIGMA_DEFAULT_SUFFIX = " (default 15% × MTTF)"
WORKSPACE_FM_INSPECTOR_MTTR = "MTTR (uur)"
WORKSPACE_FM_INSPECTOR_COST_CM = "Correctieve herstelkosten (EUR)"
WORKSPACE_FM_INSPECTOR_EFFECT_LINKS = "Effecttoekenning"
WORKSPACE_FM_INSPECTOR_EFFECT_LINKS_EMPTY = "Geen FM-effectlinks"
WORKSPACE_FM_INSPECTOR_INPUTS_MISSING = "Invoer niet beschikbaar (FM ontbreekt in project)."

SAVE_SUCCESS_STATUS = "Project opgeslagen."
SAVE_BLOCKED_WHILE_RUN = "Opslaan is pas beschikbaar na afronden van de analyse-run."
UNSAVED_DIALOG_TEXT = "Er zijn niet-opgeslagen wijzigingen. Wat wil je doen?"
SAVE_CONFLICT_MESSAGE = (
    "Het projectbestand is extern gewijzigd sinds laden. "
    "Gebruik 'Opslaan als...' om je wijzigingen veilig te bewaren."
)

ISOGRAPH_IMPORT_DIALOG_TITLE = "RCM-Cost export importeren"
ISOGRAPH_IMPORT_DIALOG_INTRO = (
    "Kies het modeljaar voor leeftijd en kalenderjaar. "
    "Bij tegenstrijdige initiële leeftijd op één locatie kiest u één waarde."
)
ISOGRAPH_IMPORT_MODELJAAR_LABEL = "Modeljaar"
ISOGRAPH_IMPORT_CONFLICTS_INTRO = (
    "Meerdere initiële leeftijden op hetzelfde bouwdeel — kies één waarde (jaren):"
)
ISOGRAPH_IMPORT_CONFLICT_ROW = "Locatie {pbs_id}"
ISOGRAPH_IMPORT_AGE_OPTION = "{age_years:.2f} jaar"

ISOGRAPH_OPEN_BUTTON_LABEL = "Open RCM-Cost export…"
ISOGRAPH_OPEN_FILE_DIALOG_TITLE = "Kies RCM-Cost Excel-export"
ISOGRAPH_OPEN_FILE_FILTER = "RCM-Cost export (*.xlsx)"
ISOGRAPH_SAVE_IMPORTED_TITLE = "Opslaan als RCM2-project"
ISOGRAPH_SAVE_IMPORTED_FILTER = "RCM project (*.rcm.json)"
ISOGRAPH_IMPORT_VALIDATION_FAILED = (
    "Het geïmporteerde project is structureel ongeldig en is niet opgeslagen."
)
ISOGRAPH_IMPORT_SAVE_SUCCESS = "RCM-Cost export opgeslagen als {path}."

PORTFOLIO_WIZARD_BUTTON_LABEL = "Portfolio samenstellen…"
PORTFOLIO_WIZARD_BUTTON_TOOLTIP = (
    "Scan een sync-root met netwerkschakel-modellen en merge geselecteerde bronnen tot één portfolio."
)
PORTFOLIO_WIZARD_TITLE = "Portfolio samenstellen"
PORTFOLIO_WIZARD_INTRO = (
    "Kies welke netwerkschakel-modellen in het portfolio worden opgenomen. "
    "Lifecycle en modeljaar blijven per bron behouden; waarschuwingen verschijnen bij afwijking."
)
PORTFOLIO_WIZARD_ROOT_LABEL = "Sync-root"
PORTFOLIO_WIZARD_NAME_LABEL = "Portfolionaam"
PORTFOLIO_WIZARD_TABLE_HEADERS = ("Netwerkschakel", "Bestand", "FM's", "Lifecycle", "Modeljaar")
PORTFOLIO_WIZARD_WARNINGS_LABEL = "Waarschuwingen"
PORTFOLIO_WIZARD_NO_RCM_JSON = "Alleen .rcm.json-bronnen worden gemerged; Excel vereist eerst import."
PORTFOLIO_OPEN_ROOT_DIALOG_TITLE = "Kies portfolio sync-root"
PORTFOLIO_SAVE_TITLE = "Portfolio opslaan"
PORTFOLIO_SAVE_FILTER = "RCM portfolio (*.rcm.json)"
PORTFOLIO_SAVE_SUCCESS = "Portfolio opgeslagen als {path}."

RCM_COST_PARITY_BUTTON_LABEL = "Modelcontrole AW…"
RCM_COST_PARITY_BUTTON_TOOLTIP = (
    "Vergelijk FM-resultaten met RCM-Cost/AW-benchmarks uit import_settings "
    "(TotalCost binnen onzekerheidsband). Vereist een run op een geïmporteerd AW-project."
)
RCM_COST_PARITY_TITLE = "Modelcontrole — RCM-Cost resultaten"
RCM_COST_PARITY_INTRO = (
    "Per faalwijze: vergelijking van RCM2-totalen met AW-export (TotalCost, TotalTdt) "
    "plus rekendiagnostiek (# falen, REV-momenten, downtime-splitsing CM/PM/inspectie, "
    "invoer leeftijd/MTTF). OK = binnen AW-onzekerheidsband; Afwijking = buiten band."
)
RCM_COST_PARITY_HEADERS = (
    "FM",
    "Omschrijving",
    "Status",
    "AW €",
    "RCM2 €",
    "Δ €",
    "Tol €",
    "AW uur",
    "RCM2 uur",
    "AW # falen",
    "RCM2 # falen",
    "Δ # falen",
    "REV actief",
    "REV jaren",
    "REV interval jr",
    "AW CM uur",
    "RCM2 CM uur",
    "AW PM uur",
    "RCM2 PM uur",
    "AW insp uur",
    "RCM2 CM €",
    "RCM2 PM €",
    "P(falen)",
    "Leeftijd jr",
    "MTTF AW",
    "MTTF RCM2",
    "PM-taken",
)
RCM_COST_PARITY_FILTER_ALL = "Alle"
RCM_COST_PARITY_FILTER_FAIL = "Alleen afwijkingen"
RCM_COST_PARITY_FILTER_PASS = "Alleen OK"
RCM_COST_PARITY_NO_BENCHMARK = (
    "Geen AW-benchmarks in import_settings. Importeer opnieuw vanuit RCM-Cost export "
    "of open een project met TotalCost per faalwijze."
)
RCM_COST_PARITY_NO_RUN = "Draai eerst een volledige analyse voordat u modelcontrole opent."
RCM_COST_PARITY_EXPORT_BUTTON = "Validatie-export…"
RCM_COST_PARITY_EXPORT_TOOLTIP = (
    "Exporteer per faalwijze counterfactual # falen naar Excel "
    "(scenario, REV, repair quality, horizon) t.o.v. AW TotalW."
)
RCM_COST_PARITY_EXPORT_TITLE = "Validatie-export opslaan"
RCM_COST_PARITY_EXPORT_FILTER = "Excel (*.xlsx)"
RCM_COST_PARITY_EXPORT_SUCCESS = "Validatie-export opgeslagen:\n{path}"
RCM_COST_PARITY_EXPORT_FAILED = "Validatie-export mislukt:\n{error}"

LIBRARY_EXPLORER_TITLE = "Faalwijze-bibliotheek"
LIBRARY_EXPLORER_INTRO = (
    "Gedistilleerde bibliotheekitems met bronvermelding. "
    "Items met meerdere bronnen zijn uniform binnen tolerantie; variant clusters tonen param-afwijking."
)
LIBRARY_EXPLORER_HEADERS = ("Omschrijving", "Categorie", "Bronnen", "Variant", "Waarde")

FM_EDITOR_TITLE = "Faalwijze bewerken — {fm_id}"
FM_EDITOR_TAB_BASIS = "Basis"
FM_EDITOR_TAB_EFFECTEN = "Effecten"
FM_EDITOR_TAB_CORRECTIEF = "Correctief"
FM_EDITOR_TAB_PREVENTIEF = "Preventief"
FM_EDITOR_FAILURE_TYPE = "Faaltype"
FM_EDITOR_MTTF = "MTTF (jaar)"
FM_EDITOR_SIGMA = "Sigma (jaar)"
FM_EDITOR_AGING_DISTRIBUTION = "Aging-verdeling"
FM_EDITOR_BETA = "Beta (Weibull)"
FM_EDITOR_NMF = "Niet-merkbaar falen (NMF)"
FM_EDITOR_OMSCHRIJVING = "Faalscenario"
FM_EDITOR_FUNCTIE = "Functie"
FM_EDITOR_REPAIR_QUALITY = "Herstelkwaliteit (0–1)"
FM_EDITOR_BOUWJAAR = "Startleeftijd (bouwjaar PBS)"
FM_EDITOR_PBS_SHARED_WARN = (
    "Let op: dit PBS-item ({pbs_id}) is gekoppeld aan {count} faalwijzen."
)
FM_EDITOR_CM_MATERIAAL = "CM materiaalkosten (EUR)"
FM_EDITOR_CM_ARBEID = "CM arbeid/engineering (EUR)"
FM_EDITOR_DOWNTIME_HOURS = "Hersteltijd per falen (uur)"
FM_EDITOR_NOTES = "Scenario-notities"
FM_EDITOR_AANNAME_CM = "Aanname CM-kosten"
FM_EDITOR_AANNAME_DOWNTIME = "Aanname downtime"
FM_EDITOR_VALIDATION_TITLE = "Bewerken niet opgeslagen"
FM_EDITOR_COMMIT_FAILED = "Opslaan mislukt: {detail}"
FM_EDITOR_COMMIT_BUSY = "Faalwijze opslaan en herberekenen…"
GRID_DIRTY_GUARD_TITLE = "Onopgeslagen invoerwijzigingen"
GRID_DIRTY_GUARD_TEXT = (
    "Er zijn onopgeslagen invoerwijzigingen in de invoertabellen. Wat wilt u doen?"
)
GRID_DIRTY_SAVE = "Invoer opslaan"
GRID_DIRTY_DISCARD = "Invoer verwerpen"
GRID_DIRTY_CANCEL_EDITOR = "Editor annuleren"
GRID_DIRTY_CANCEL_SHUTDOWN = "Niet afsluiten"
GRID_DIRTY_SAVE_FAILED_DETAIL = "Invoer opslaan mislukt."
SHUTDOWN_BUSY_TITLE = "Achtergrondtaak actief"
SHUTDOWN_BUSY_TEXT = (
    "Er draait nog een berekening op de achtergrond. Afsluiten annuleert die taak. "
    "Wilt u toch afsluiten?"
)
SHUTDOWN_BUSY_CONFIRM = "Afsluiten"
SHUTDOWN_BUSY_CANCEL = "Annuleren"
WORKSPACE_MENU_EXPORT_RCM_COST = "RCM-Cost exporteren…"
ISOGRAPH_EXPORT_FILE_DIALOG_TITLE = "RCM-Cost export opslaan"
ISOGRAPH_EXPORT_MISSING_SOURCE_TITLE = "AW-bron ontbreekt"
ISOGRAPH_EXPORT_MISSING_SOURCE_TEXT = (
    "De originele AW-workbook (bron-sidecar) ontbreekt. Kies het bronbestand om de "
    "export te kunnen uitvoeren."
)
ISOGRAPH_EXPORT_SUMMARY_TITLE = "Export voltooid"
ISOGRAPH_EXPORT_SUMMARY_BODY = (
    "Gepatcht: {patched}\nToegevoegd: {added}\nWaarschuwingen: {warned}"
)
WORKSPACE_MENU_FAALWIJZEN_BATCH = "Faalwijzen batch-bewerken"
FM_EDITOR_FM_LINKS = "Effect bij falen"
FM_EDITOR_PM_LINKS = "Effect bij PM-taken"
FM_EDITOR_EFFECT_KLASSEN = "Gekoppelde effectklassen"
FM_EDITOR_ADD_ROW = "Rij toevoegen"
FM_EDITOR_REMOVE_ROW = "Rij verwijderen"
FM_EDITOR_PM_TASKS = "PM-taken"
FM_EDITOR_TASK_GROUP = "Taakgroep (gedeeld)"
FM_EDITOR_TASK_GROUP_SHARED_WARN = (
    "Taakgroep {group_id} wordt ook door andere faalwijzen gebruikt."
)
FM_EDITOR_TASK_GROUP_NONE = "(geen)"
FM_EDITOR_WARN_AGING_WITHOUT_REV = (
    "Faaltype is veroudering (aging), maar er is geen REV-taak op deze faalwijze. "
    "Overweeg een REV-taak toe te voegen."
)
FM_EDITOR_WARN_REV_WITHOUT_AGING = (
    "Er is een REV-taak, maar het faaltype is geen veroudering (aging). "
    "Controleer of faaltype en REV-taken bij elkaar passen."
)
FM_EDITOR_WARN_PM_BUNDLE_SUGGEST = (
    "PM-taak {pm_id}: dezelfde maatregel komt op {count} ander(e) component(en) voor "
    "zonder taakgroep — overweeg een gedeelde taakgroep."
)
FM_EDITOR_NO_PROJECT = "Laad eerst een project voordat je een faalwijze bewerkt."
FM_EDITOR_NEW_FM = "Nieuwe faalwijze"
FM_EDITOR_NEW_FM_TOOLTIP = "Voeg een faalwijze toe op de geselecteerde leaf-PBS in de sidebar."
FM_EDITOR_NEW_FM_NO_LEAF_PBS = (
    "Selecteer één leaf-PBS in de sidebar om een nieuwe faalwijze toe te voegen."
)
FM_EDITOR_TITLE_CREATE = "Nieuwe faalwijze — {fm_id}"
FM_EDITOR_PBS_FIXED = "PBS (vast)"
FM_EDITOR_CREATE_OMSCHRIJVING_REQUIRED = "Vul een faalscenario in voordat je opslaat."
FM_EDITOR_CREATE_FUNCTIE_REQUIRED = "Selecteer een functie voordat je opslaat."
FM_EDITOR_SAVE = "Opslaan"
FM_EDITOR_SAVE_AND_CLOSE = "Opslaan en sluiten"
FM_EDITOR_CANCEL_DIRTY = (
    "Er zijn wijzigingen sinds de laatste opslag. Sluiten zonder op te slaan?"
)
FM_EDITOR_FILL_FROM = "Vul van…"
FM_EDITOR_TAB_RESULTATEN = "Resultaten"
FM_EDITOR_LINK_MEASURE = "Koppel aan bestaande maatregel…"
FM_EDITOR_NEW_TASK_GROUP = "Nieuwe taakgroep…"
FM_EDITOR_RESULTS_EMPTY = "Opslaan om resultaten te berekenen."
FM_EDITOR_FILL_FROM_CONFIRM = (
    "Basis en Correctief van {fm_id} overschrijven huidige invoer?"
)
FM_EDITOR_FILL_FROM_TITLE = "Vul van faalwijze"
FM_EDITOR_LINK_MEASURE_TITLE = "Koppel aan maatregel"
FM_EDITOR_NEW_TASK_GROUP_TITLE = "Nieuwe taakgroep"

MODEL_SETTINGS_BUTTON_LABEL = "Modelinstellingen"
MODEL_SETTINGS_SECTION_PROJECT = "Project"
MODEL_SETTINGS_SECTION_HORIZON = "Horizon & tijd"
MODEL_SETTINGS_SECTION_AGING = "Veroudering (defaults)"
MODEL_SETTINGS_SECTION_FAILPARAMS = "Standaard faalparameters"
MODEL_SETTINGS_SECTION_MONTE_CARLO = "Monte Carlo"
MODEL_SETTINGS_PROJECTNAAM = "Projectnaam"
MODEL_SETTINGS_MODELLEUR = "Modelleur"
MODEL_SETTINGS_LIFECYCLE = "LCC-periode (jaar)"
MODEL_SETTINGS_AW_MC_HORIZON = "AW MC-horizon (LifeTime vooruit)"
MODEL_SETTINGS_AW_MC_HORIZON_TTIP = (
    "Studieduur = LCC-periode vooruit vanaf huidige leeftijd (AW Monte Carlo / TotalW). "
    "Uit: studieduur tot leeftijd LCC-periode (resterend). "
    "Zet aan na herimport als validatie-export A2 (LifeTime-semantiek) dominant is; "
    "combineer met CM-overlay (automatisch uit import) en validatie-export."
)
MODEL_SETTINGS_MODELJAAR = "Modeljaar"
MODEL_SETTINGS_BUCKET_INTERVAL = "Bucket-interval"
MODEL_SETTINGS_BUCKET_INTERVAL_VALUE = "1 kalenderjaar (vast)"
MODEL_SETTINGS_DEFAULT_MTTF_MULTIPLIER = "MTTF-multiplier (× ontwerpleeftijd)"
MODEL_SETTINGS_DEFAULT_MTTF_MULTIPLIER_TTIP = (
    "Beïnvloedt vooral standaard-MTTF op PBS-niveau; bestaande faalwijze-MTTF's worden niet retroactief gewijzigd."
)
MODEL_SETTINGS_DEFAULT_SIGMA_FRACTION = "Sigma-fractie (× MTTF bij σ=0)"
MODEL_SETTINGS_DEFAULT_AGING_DISTRIBUTION = "Default verouderingsdistributie"
MODEL_SETTINGS_DEFAULT_BETA = "Default beta (Weibull)"
MODEL_SETTINGS_APPLY_AGING = "Toepassen op alle aging-faalwijzen"
MODEL_SETTINGS_APPLY_AGING_CONFIRM = (
    "{count} aging-faalwijzen krijgen {dist}."
    + "{beta_line} Doorgaan?"
)
MODEL_SETTINGS_APPLY_AGING_BETA_LINE = " Beta={beta:.2f}."
MODEL_SETTINGS_MONTE_CARLO_N = "Aantal simulaties"
MODEL_SETTINGS_MONTE_CARLO_SEED = "Random seed"
MODEL_SETTINGS_MONTE_CARLO_DISABLED_TTIP = "Monte Carlo nog niet actief in desktop."
MODEL_SETTINGS_RERUN_CHECKBOX = "Direct herberekenen"
MODEL_SETTINGS_RERUN_REQUIRED = "Herbereken vereist — modelinstellingen zijn gewijzigd."
MODEL_SETTINGS_VALIDATION_TITLE = "Modelinstellingen niet opgeslagen"
MODEL_SETTINGS_COMMIT_FAILED = "Opslaan mislukt: {detail}"
MODEL_SETTINGS_NO_PROJECT = "Laad eerst een project voordat je modelinstellingen opent."

# Rapportage (slice 57)
REPORT_GENERATE_BUTTON_LABEL = "Rapport genereren…"
REPORT_GENERATE_BUTTON_TOOLTIP = (
    "Standaard projectbreed rapport (Word, optioneel PDF). "
    "Werkruimte-filters en taaktype-filters worden niet overgenomen."
)
REPORT_INELIGIBLE_NO_RUN = (
    "Geen voltooide analyse-run beschikbaar. Start Run → A of een analyse-run."
)
REPORT_DIALOG_TITLE = "Rapport genereren"
REPORT_DIALOG_OUTPUT_PATH = "Outputbestand (.docx)"
REPORT_DIALOG_GENERATE_PDF = "Ook PDF genereren"
REPORT_DIALOG_NB_THRESHOLD = "Drempel niet-beschikbaarheid (% van scope)"
REPORT_DIALOG_COST_THRESHOLD = "Drempel kosten (% van scope)"
REPORT_DIALOG_INCLUDE_BELOW = "Neem functies onder drempel ook op"
REPORT_DIALOG_PBS_DEEPDIVE = "Beperk tot geselecteerd PBS-onderdeel"
REPORT_DIALOG_PREVIEW = "Voorvertoning"
REPORT_DIALOG_PREVIEW_TEMPLATE = (
    "Modus: {mode} — NB-functies: {nb_pages}, kosten-functies: {cost_pages}"
)
REPORT_GENERATION_BUSY = "Rapport wordt gegenereerd…"
REPORT_GENERATION_FAILED_TITLE = "Rapport mislukt"
REPORT_PDF_FAILED_TITLE = "PDF-conversie mislukt"
REPORT_PDF_FAILED_BODY = (
    "Het Word-document is wel opgeslagen:\n{docx_path}\n\n{detail}"
)
REPORT_SECTION_COVER = "Voorblad"
REPORT_SECTION_KPI = "KPI's"
REPORT_SECTION_PROJECT_NB = "Project — niet-beschikbaarheid"
REPORT_SECTION_PROJECT_LCC = "Project — lifecycle kosten"
REPORT_SECTION_APPENDIX = "Appendix"
REPORT_COVER_SCENARIO_SINGLE = "Enkele analyse"
REPORT_COVER_SCENARIO_COMPARE = "Vergelijking A ↔ B"
REPORT_KPI_CONTEXT_TEMPLATE = "LCC-periode: {lifecycle_years} jaar — modeljaar: {modeljaar}"
REPORT_APPENDIX_NB_PROXY = WORKSPACE_UNAVAILABILITY_PROXY_DISCLAIMER
REPORT_APPENDIX_BELOW_THRESHOLD = (
    "{nb_count} NB-functie(s) en {cost_count} kosten-functie(s) onder drempel weggelaten."
)
REPORT_APPENDIX_NB_OVER_100 = (
    "Som van functie-NB kan >100% zijn wanneer functies parallel uitvallen."
)
REPORT_NARRATIVE_SCENARIO_MISMATCH = (
    "Let op: scenario A en B gebruiken verschillende scenario-keys; vergelijk interpretatie voorzichtig."
)


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, "Onbekende status")
