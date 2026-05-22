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
WORKSPACE_WINDOW_TITLE = "RCM2 desktop — resultatenwerkruimte"
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
WORKSPACE_MODE_LCC = "Tijdsplot"
WORKSPACE_MODE_FM_DETAIL = "FM-detail"

WORKSPACE_TOP10_SUBBAR_LABEL = "Top 10:"
WORKSPACE_SOURCE_TOGGLE_PBS = "Component"
WORKSPACE_SOURCE_TOGGLE_FAALWIJZE = "Faalwijze"

WORKSPACE_METRIC_NIET_BESCHIKBAARHEID = "Niet-beschikbaarheid"
WORKSPACE_METRIC_KOSTEN = "Kosten"
WORKSPACE_METRIC_FAALMOMENTEN = "Faalmomenten"

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
WORKSPACE_MEEKOPPEL_WHATIF_HINT = "Schakel what-if planning in om meekoppelkansen te zien."
WORKSPACE_MEEKOPPEL_EMPTY = "Geen meekoppelkansen voor het gekozen tijdsvenster."
WORKSPACE_MEEKOPPEL_WINDOW_LABEL = "Tijdsvenster (jaren):"
WORKSPACE_MEEKOPPEL_PREVIEW = "Preview"
WORKSPACE_MEEKOPPEL_APPLY = "Toepassen"
WORKSPACE_MEEKOPPEL_SELECT_ROW = "Selecteer een suggestie in de tabel."
WORKSPACE_MEEKOPPEL_PREVIEW_TITLE = "Preview meekoppelen"
WORKSPACE_MEEKOPPEL_PREVIEW_ANCHOR_EARLIER = "Anker: vroegste due-jaar"
WORKSPACE_MEEKOPPEL_PREVIEW_ANCHOR_LATER = "Anker: laatste due-jaar"
WORKSPACE_MEEKOPPEL_PREVIEW_BODY = (
    "PM {shifted}: jaar {from_year} → {to_year} (verschuiving {shift} jaar).\n"
    "Paar: {pm_a} / {pm_b}."
)
WORKSPACE_MEEKOPPEL_PREVIEW_BLOCKED = "Geen shift mogelijk: {reason}"
WORKSPACE_MEEKOPPEL_HEADER_ELEMENT = "Element"
WORKSPACE_MEEKOPPEL_HEADER_PM_A = "PM A"
WORKSPACE_MEEKOPPEL_HEADER_PM_B = "PM B"
WORKSPACE_MEEKOPPEL_HEADER_JAAR_A = "Jaar A"
WORKSPACE_MEEKOPPEL_HEADER_JAAR_B = "Jaar B"
WORKSPACE_MEEKOPPEL_HEADER_DELTA = "Δ"
WORKSPACE_MEEKOPPEL_HEADER_REDEN = "Reden"
WORKSPACE_KPI_COLLAPSE_TOOLTIP = "KPI-paneel in- of uitklappen (alleen Tijdsplot-modus)."
WORKSPACE_KPI_PANEL_TITLE = "KPI — huidige analyse"
WORKSPACE_PM_MODE_REDIRECT = (
    "Planning en PM-inzicht zitten nu in de LCC-modus (filters en jaardetail)."
)
WORKSPACE_FM_EVIDENT_FILTER_ALL = "Alle"
WORKSPACE_FM_EVIDENT_FILTER_NMF = "Alleen NMF"
WORKSPACE_FM_EVIDENT_FILTER_EVIDENT = "Alleen evident"

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


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, "Onbekende status")
