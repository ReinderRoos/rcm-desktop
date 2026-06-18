# PRD — Slice 75: FM-detail viewport-autofit + Bijsnijden (regelomloop)



**Status:** in-progress (semantiek herzien 2026-06-11)

**Voorganger:** slice 62 (werkruimte-panelen), slice 18 (tekstomloop), slice 25 (schaalbare kolombreedtes)

**Datum:** 2026-06-11

**Triage:** `ready-for-agent`



> Synthese van een `/grill-with-docs`-sessie (2026-06-11). Wens 2 van 5.

> **Herziening:** gebruiker verduidelijkte dat Autofit = alle kolommen binnen viewport;

> Bijsnijden = regelomloop uit (enkele regel), niet elide met cap.



---



## Problem Statement



In de **FM-detail-tabel** (`FMResultsTableModel`) zijn lange faalwijze-omschrijvingen

en bouwdeelnamen lastig te scannen. De analist wil:



1. **Altijd alle kolommen op één scherm** zien (ook met PBS-boom zichtbaar), zonder

   horizontaal scrollen.

2. **Tekst standaard over meerdere regels** laten lopen (regelomloop), met een

   schakelaar om terug te gaan naar compacte enkele-regelweergave.



## Solution



Vanuit de gebruiker gezien:



- **Autofit (altijd aan):** kolommen verdelen de beschikbare horizontale ruimte van de

  tabel. Compacte kolommen (FM-id, PBS-id, numeriek) nemen minimale inhoudsbreedte;

  tekstkolommen (Faalwijze, Bouwdeel) vullen het resterende deel (`Stretch`). Geen

  horizontale scrollbar nodig.

- **Bijsnijden-schakelaar (`<Bijsnijden>`, standaard uit):** zet **regelomloop uit**

  (enkele regel per cel). Uit = omloop aan (standaard); aan = bijsnijden / compact.

  Bij enkele regel mag tekst die niet past worden ge-elideerd met "…" + tooltip.

- De gekozen omloop-voorkeur **blijft bewaard** tussen sessies (`QSettings`).



---



## Zoom-out: modulekaart



```

        FM-detail-panel (fm_detail_workspace_panel.py)

                 │  fm_table_view + <Bijsnijden>-knop

                 ▼

   workspace_table_policy.py

        apply_fm_detail_viewport_fit()     ← altijd: Stretch + ResizeToContents-mix

        apply_fm_detail_display_mode()     ← regelomloop aan/uit + delegate

                 │

                 ▼

        column_fit_policy.py (Qt-vrij)

        ColumnFitMode + viewport-kolomplan + display-beslissing

                 │

                 ▼

        QSettings  (workspace/fm_detail/column_fit_mode)

```



---



## Implementation Decisions



### Besloten ontwerpkeuzes (herzien)



- **Autofit = viewport-fit (`viewport_fit_always`).** Kolombreedtes worden niet

  gedreven door `ResizeToContents` op alle kolommen. Mix: `ResizeToContents` op

  id-/numerieke kolommen; `Stretch` op Faalwijze (kolom 1) en Bouwdeel (kolom 3).

- **Bijsnijden = regelomloop uit (`crop_is_single_line`).** Aan = geen word wrap;

  uit = word wrap (standaard). Niet: vaste kolomcap + elide als primaire modus.

- **Elide alleen bij enkele regel.** Wanneer bijsnijden aan staat en tekst breder is

  dan de cel, `Qt.ElideRight` + tooltip.

- **Persistentie:** bestaande sleutel `workspace/fm_detail/column_fit_mode` behouden;

  waarden `passend` (= omloop aan) / `bijgesneden` (= omloop uit).



### Kolomplan FM-detail (7 kolommen)



| Kolom | Veld | Resize-modus |

|-------|------|--------------|

| 0 | fm_id | ResizeToContents |

| 1 | faalwijze_omschrijving | Stretch |

| 2 | pbs_id | ResizeToContents |

| 3 | bouwdeel_naam | Stretch |

| 4–6 | numeriek | ResizeToContents |



### Architectuurprincipes (AGENTS.md)



- Qt-vrije beslissing in `adapter/column_fit_policy.py`; Qt-binding in

  `views/panels/workspace_table_policy.py`.

- Geen modelwijziging.



---



## User Stories



1. Als analist wil ik alle FM-detail-kolommen tegelijk zien zonder horizontaal te

   scrollen, ook met PBS-boom open.

2. Als analist wil ik faalwijze-tekst standaard over meerdere regels zien (omloop aan).

3. Als analist wil ik met `<Bijsnijden>` omloop uitzetten voor een compacte tabel.

4. Als analist wil ik bij enkele regel nog steeds de volledige tekst via tooltip.

5. Als analist wil ik dat mijn omloop-voorkeur bewaard blijft tussen sessies.



---



## Testing Decisions



- **Qt-vrij:** `decide_column_fit` → `word_wrap` + `elide_enabled`; viewport-kolomplan.

- **pytest-qt:** viewport gebruikt Stretch op tekstkolommen; knop schakelt `wordWrap`;

  persistentie via QSettings.



---



## Out of Scope



- Per-kolom handmatige breedte-persistentie.

- LCC-/PBS-tabellen (policy is herbruikbaar ontworpen).

- Kolommen herordenen/verbergen.



## Further Notes



- Slice 76 menubalk-item `view.column_crop` deelt dezelfde `state_source`.

- Prior art: slice 18 (`SETTINGS_TABLE_WORD_WRAP_KEY`, `resize_rows_if_wrapped_within_limit`).


