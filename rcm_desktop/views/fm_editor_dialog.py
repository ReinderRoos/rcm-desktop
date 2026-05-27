"""Modale faalwijze-editor (slice 44) — alleen layout; logica via adapter."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.cm_cost_split_mapper import split_cm_cost
from rcm_desktop.adapter.fm_edit_bundle_assembler import FmEditDraft, assemble_bundle
from rcm_desktop.adapter.fm_edit_bundle_service import (
    FmEditBundle,
    count_faalwijzen_for_pbs_in_edit,
    count_faalwijzen_for_task_group_in_edit,
)
from rcm_desktop.adapter.fm_edit_commit_facade import RunPolicy, commit_fm_edit
from rcm_desktop.adapter.fm_edit_commit_runner import FmEditCommitRunner
from rcm_desktop.adapter.fm_edit_commit_service import (
    FmEditCommitResult,
    create_edit_session,
)
from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope
from rcm_desktop.adapter.fm_edit_row_mappers import downtime_hours_from_row
from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.fk_normalization import normalize_optional_fk
from rcm_desktop.adapter.fm_edit_consistency import findings_for_edit_rows
from rcm_desktop.adapter.fm_sigma_coupling import coupled_sigma, is_sigma_manual
from rcm_desktop.adapter.pm_task_group_delegate import PmTaskGroupDelegate


def _new_id(prefix: str, existing: set[str]) -> str:
    n = 1
    while True:
        candidate = f"{prefix}-{n:03d}"
        if candidate not in existing:
            return candidate
        n += 1


class FmEditorDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        project,
        fm_id: str,
        project_path: str | Path | None = None,
        save_to_disk: bool = False,
        baseline_mtime_ns: int | None = None,
        editing_session: EditingSession | None = None,
    ) -> None:
        super().__init__(parent)
        self._project = project
        self._fm_id = fm_id
        self._path = Path(project_path) if project_path else None
        self._save_to_disk = save_to_disk
        self._baseline_mtime_ns = baseline_mtime_ns
        if editing_session is not None:
            self._session = editing_session
            self._bundle = load_fm_edit_scope(editing_session, fm_id)
        else:
            self._session = create_edit_session(project)
            self._bundle = load_fm_edit_scope(project, fm_id)
        self.commit_result: FmEditCommitResult | None = None
        self._commit_runner = FmEditCommitRunner()
        self._commit_runner.finished.connect(self._on_commit_finished)
        self._progress: QProgressDialog | None = None
        self._functie_ids = tuple(sorted(project.functies.keys()))

        self.setWindowTitle(
            messages.FM_EDITOR_TITLE.format(fm_id=fm_id)
        )
        self.setMinimumSize(720, 520)

        root = QVBoxLayout(self)
        intro = QLabel(
            f"{self._bundle.faalwijze_row.get('faalwijze_omschrijving', '')} — "
            f"PBS {self._bundle.pbs_row.get('bouwdeel_naam', self._bundle.pbs_row.get('pbs_id', ''))}"
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_basis_tab(), messages.FM_EDITOR_TAB_BASIS)
        self._tabs.addTab(self._build_effecten_tab(), messages.FM_EDITOR_TAB_EFFECTEN)
        self._tabs.addTab(self._build_correctief_tab(), messages.FM_EDITOR_TAB_CORRECTIEF)
        self._tabs.addTab(self._build_preventief_tab(), messages.FM_EDITOR_TAB_PREVENTIEF)
        root.addWidget(self._tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _build_basis_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        self._failure_type = QComboBox()
        self._failure_type.addItem("random", "random")
        self._failure_type.addItem("aging", "aging")
        ft = str(self._bundle.faalwijze_row.get("failure_type", "random"))
        idx = self._failure_type.findData(ft)
        self._failure_type.setCurrentIndex(max(0, idx))
        form.addRow(messages.FM_EDITOR_FAILURE_TYPE, self._failure_type)

        self._mttf = QDoubleSpinBox()
        self._mttf.setRange(0.01, 10_000.0)
        self._mttf.setDecimals(2)
        self._mttf.setValue(float(self._bundle.faalwijze_row.get("mttf_jaar") or 1.0))
        form.addRow(messages.FM_EDITOR_MTTF, self._mttf)

        self._sigma = QDoubleSpinBox()
        self._sigma.setRange(0.0, 10_000.0)
        self._sigma.setDecimals(2)
        self._sigma.setValue(float(self._bundle.faalwijze_row.get("sigma_jaar") or 0.0))
        form.addRow(messages.FM_EDITOR_SIGMA, self._sigma)
        self._aging_distribution = QComboBox()
        self._aging_distribution.addItem("Normal", "normal")
        self._aging_distribution.addItem("Links-afgeknipt normal 0+", "truncated_normal_0")
        self._aging_distribution.addItem("Weibull 2p", "weibull_2p")
        cur_dist = str(self._bundle.faalwijze_row.get("aging_distribution") or "normal")
        dist_idx = self._aging_distribution.findData(cur_dist)
        self._aging_distribution.setCurrentIndex(max(0, dist_idx))
        form.addRow(messages.FM_EDITOR_AGING_DISTRIBUTION, self._aging_distribution)
        self._beta = QDoubleSpinBox()
        self._beta.setRange(0.0, 100.0)
        self._beta.setDecimals(3)
        self._beta.setValue(float(self._bundle.faalwijze_row.get("beta_jaar") or 0.0))
        form.addRow(messages.FM_EDITOR_BETA, self._beta)
        self._last_mttf = self._mttf.value()
        self._mttf.valueChanged.connect(self._on_mttf_changed)
        self._failure_type.currentIndexChanged.connect(self._refresh_consistency_warnings)
        self._failure_type.currentIndexChanged.connect(self._refresh_aging_fields_visibility)
        self._aging_distribution.currentIndexChanged.connect(self._refresh_aging_fields_visibility)
        self._basis_warn = QLabel()
        self._basis_warn.setWordWrap(True)
        self._basis_warn.setStyleSheet("color: #E65100;")
        form.addRow(self._basis_warn)

        self._nmf = QCheckBox(messages.FM_EDITOR_NMF)
        self._nmf.setChecked(not bool(self._bundle.faalwijze_row.get("is_evident", True)))
        form.addRow(self._nmf)

        self._omschrijving = QLineEdit(
            str(self._bundle.faalwijze_row.get("faalwijze_omschrijving") or "")
        )
        form.addRow(messages.FM_EDITOR_OMSCHRIJVING, self._omschrijving)

        self._functie = QComboBox()
        for fid in self._functie_ids:
            self._functie.addItem(fid, fid)
        cur_f = str(self._bundle.faalwijze_row.get("functie_id") or "")
        fi = self._functie.findData(cur_f)
        if fi >= 0:
            self._functie.setCurrentIndex(fi)
        form.addRow(messages.FM_EDITOR_FUNCTIE, self._functie)

        self._repair_quality = QDoubleSpinBox()
        self._repair_quality.setRange(0.0, 1.0)
        self._repair_quality.setSingleStep(0.05)
        self._repair_quality.setValue(
            float(self._bundle.faalwijze_row.get("repair_quality") or 1.0)
        )
        form.addRow(messages.FM_EDITOR_REPAIR_QUALITY, self._repair_quality)

        self._bouwjaar = QSpinBox()
        self._bouwjaar.setRange(1900, 2200)
        self._bouwjaar.setValue(int(self._bundle.pbs_row.get("bouwjaar") or 0))
        form.addRow(messages.FM_EDITOR_BOUWJAAR, self._bouwjaar)

        pbs_id = str(self._bundle.pbs_row.get("pbs_id") or "")
        shared = count_faalwijzen_for_pbs_in_edit(self._session, pbs_id)
        if shared > 1:
            warn = QLabel(
                messages.FM_EDITOR_PBS_SHARED_WARN.format(pbs_id=pbs_id, count=shared)
            )
            warn.setWordWrap(True)
            warn.setStyleSheet("color: #E65100;")
            form.addRow(warn)

        self._refresh_aging_fields_visibility()
        return page

    def _refresh_aging_fields_visibility(self) -> None:
        is_aging = str(self._failure_type.currentData() or "random") == "aging"
        dist = str(self._aging_distribution.currentData() or "normal")
        show_beta = is_aging and dist == "weibull_2p"
        self._aging_distribution.setVisible(is_aging)
        self._beta.setVisible(show_beta)
        self._sigma.setVisible(is_aging and dist != "weibull_2p")

    def _build_correctief_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        split = split_cm_cost(
            float(self._bundle.faalwijze_row.get("cost_cm_eur") or 0.0),
            hint=str(self._bundle.faalwijze_row.get("aanname_cm_kosten") or ""),
        )
        self._cm_materiaal = QDoubleSpinBox()
        self._cm_materiaal.setRange(0.0, 1e12)
        self._cm_materiaal.setDecimals(2)
        self._cm_materiaal.setValue(split.materiaal_eur)
        form.addRow(messages.FM_EDITOR_CM_MATERIAAL, self._cm_materiaal)

        self._cm_arbeid = QDoubleSpinBox()
        self._cm_arbeid.setRange(0.0, 1e12)
        self._cm_arbeid.setDecimals(2)
        self._cm_arbeid.setValue(split.arbeid_eur)
        form.addRow(messages.FM_EDITOR_CM_ARBEID, self._cm_arbeid)

        self._downtime_hr = QDoubleSpinBox()
        self._downtime_hr.setRange(0.0, 1e7)
        self._downtime_hr.setDecimals(2)
        self._downtime_hr.setValue(downtime_hours_from_row(self._bundle.faalwijze_row))
        form.addRow(messages.FM_EDITOR_DOWNTIME_HOURS, self._downtime_hr)

        self._notes = QTextEdit(str(self._bundle.faalwijze_row.get("notes") or ""))
        form.addRow(messages.FM_EDITOR_NOTES, self._notes)

        self._aanname_cm = QLineEdit(
            str(self._bundle.faalwijze_row.get("aanname_cm_kosten") or "")
        )
        form.addRow(messages.FM_EDITOR_AANNAME_CM, self._aanname_cm)

        self._aanname_downtime = QLineEdit(
            str(self._bundle.faalwijze_row.get("aanname_downtime") or "")
        )
        form.addRow(messages.FM_EDITOR_AANNAME_DOWNTIME, self._aanname_downtime)
        return page

    def _make_table(self, headers: tuple[str, ...]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(list(headers))
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _format_table_cell(self, col: str, val: Any) -> str:
        if col == "task_group_id":
            if normalize_optional_fk(val) is None:
                return messages.FM_EDITOR_TASK_GROUP_NONE
            return str(val)
        if val is None:
            return ""
        return str(val)

    def _fill_table(self, table: QTableWidget, rows: list[dict[str, Any]], columns: tuple[str, ...]) -> None:
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, col in enumerate(columns):
                val = row.get(col, "")
                table.setItem(
                    r_idx, c_idx, QTableWidgetItem(self._format_table_cell(col, val))
                )

    def _read_table(self, table: QTableWidget, columns: tuple[str, ...]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for r in range(table.rowCount()):
            row: dict[str, Any] = {}
            for c, col in enumerate(columns):
                item = table.item(r, c)
                text = item.text().strip() if item else ""
                if col == "fractie":
                    row[col] = float(text) if text else 0.0
                elif col in ("cost_gevolg_eur", "interval_jaar", "cost_eur"):
                    row[col] = float(text.replace(",", ".")) if text else 0.0
                elif col == "task_group_id":
                    if text == messages.FM_EDITOR_TASK_GROUP_NONE:
                        row[col] = None
                    else:
                        row[col] = normalize_optional_fk(text) or ""
                else:
                    row[col] = text
            out.append(row)
        return out

    def _build_effecten_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        fm_cols = ("link_id", "klasse_id", "fractie", "aanname_fractie")
        layout.addWidget(QLabel(messages.FM_EDITOR_FM_LINKS))
        self._fm_links_table = self._make_table(fm_cols)
        self._fill_table(self._fm_links_table, list(self._bundle.fm_effect_rows), fm_cols)
        fm_btns = QHBoxLayout()
        add_fm = QPushButton(messages.FM_EDITOR_ADD_ROW)
        add_fm.clicked.connect(lambda: self._add_link_row(self._fm_links_table, "FMEL", self._fm_id))
        rem_fm = QPushButton(messages.FM_EDITOR_REMOVE_ROW)
        rem_fm.clicked.connect(lambda: self._remove_selected_rows(self._fm_links_table))
        fm_btns.addWidget(add_fm)
        fm_btns.addWidget(rem_fm)
        fm_btns.addStretch(1)
        layout.addWidget(self._fm_links_table)
        layout.addLayout(fm_btns)

        pm_cols = ("link_id", "pm_id", "klasse_id", "fractie", "aanname_fractie")
        layout.addWidget(QLabel(messages.FM_EDITOR_PM_LINKS))
        self._pm_links_table = self._make_table(pm_cols)
        self._fill_table(self._pm_links_table, list(self._bundle.pm_effect_rows), pm_cols)
        pm_btns = QHBoxLayout()
        add_pm = QPushButton(messages.FM_EDITOR_ADD_ROW)
        add_pm.clicked.connect(self._add_pm_effect_row)
        rem_pm = QPushButton(messages.FM_EDITOR_REMOVE_ROW)
        rem_pm.clicked.connect(lambda: self._remove_selected_rows(self._pm_links_table))
        pm_btns.addWidget(add_pm)
        pm_btns.addWidget(rem_pm)
        pm_btns.addStretch(1)
        layout.addWidget(self._pm_links_table)
        layout.addLayout(pm_btns)

        ek_cols = ("klasse_id", "omschrijving", "categorie", "cost_gevolg_eur")
        layout.addWidget(QLabel(messages.FM_EDITOR_EFFECT_KLASSEN))
        self._effect_table = self._make_table(ek_cols)
        self._fill_table(self._effect_table, list(self._bundle.effect_klasse_rows), ek_cols)
        layout.addWidget(self._effect_table)
        return page

    def _build_preventief_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        pm_cols = (
            "pm_id",
            "taak_type",
            "taak_omschrijving",
            "interval_jaar",
            "cost_eur",
            "task_group_id",
        )
        layout.addWidget(QLabel(messages.FM_EDITOR_PM_TASKS))
        self._task_group_rows = {
            str(r.get("group_id")): dict(r) for r in self._bundle.task_group_rows
        }
        self._pm_tasks_table = self._make_table(pm_cols)
        rows = []
        for row in self._bundle.pm_task_rows:
            flat = dict(row)
            flat["taak_type"] = (
                flat.get("taak_type", {}).get("value")
                if isinstance(flat.get("taak_type"), dict)
                else flat.get("taak_type", "")
            )
            rows.append(flat)
        self._fill_table(self._pm_tasks_table, rows, pm_cols)
        tg_ids = tuple(sorted(self._task_group_rows.keys()))
        self._pm_tasks_table.setItemDelegateForColumn(
            5, PmTaskGroupDelegate(tg_ids, self._pm_tasks_table)
        )
        self._pm_tasks_table.itemChanged.connect(self._on_pm_table_changed)
        self._pm_tasks_table.itemSelectionChanged.connect(self._on_pm_task_selected)
        pm_btns = QHBoxLayout()
        add_pm = QPushButton(messages.FM_EDITOR_ADD_ROW)
        add_pm.clicked.connect(self._add_pm_task_row)
        rem_pm = QPushButton(messages.FM_EDITOR_REMOVE_ROW)
        rem_pm.clicked.connect(lambda: self._remove_selected_rows(self._pm_tasks_table))
        pm_btns.addWidget(add_pm)
        pm_btns.addWidget(rem_pm)
        pm_btns.addStretch(1)
        layout.addWidget(self._pm_tasks_table)
        layout.addLayout(pm_btns)

        tg_form = QFormLayout()
        self._tg_group_id = QLineEdit()
        tg_form.addRow("group_id", self._tg_group_id)
        self._tg_interval = QDoubleSpinBox()
        self._tg_interval.setRange(0.01, 500.0)
        tg_form.addRow("interval_jaar", self._tg_interval)
        self._tg_cost = QDoubleSpinBox()
        self._tg_cost.setRange(0.0, 1e12)
        tg_form.addRow("cost_eur", self._tg_cost)
        self._tg_warn = QLabel()
        self._tg_warn.setWordWrap(True)
        self._tg_warn.setStyleSheet("color: #E65100;")
        tg_form.addRow(self._tg_warn)
        layout.addWidget(QLabel(messages.FM_EDITOR_TASK_GROUP))
        layout.addLayout(tg_form)
        self._preventief_warn = QLabel()
        self._preventief_warn.setWordWrap(True)
        self._preventief_warn.setStyleSheet("color: #E65100;")
        layout.addWidget(self._preventief_warn)
        self._refresh_consistency_warnings()
        return page

    def _add_link_row(self, table: QTableWidget, prefix: str, _fm_id: str) -> None:
        existing = set()
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            if item:
                existing.add(item.text().strip())
        link_id = _new_id(prefix, existing)
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(link_id))
        table.setItem(row, 1, QTableWidgetItem(""))
        table.setItem(row, 2, QTableWidgetItem("1.0"))
        if table.columnCount() > 3:
            table.setItem(row, 3, QTableWidgetItem(""))

    def _add_pm_effect_row(self) -> None:
        pm_id = self._selected_pm_id()
        if not pm_id:
            return
        existing = {
            self._pm_links_table.item(r, 0).text().strip()
            for r in range(self._pm_links_table.rowCount())
            if self._pm_links_table.item(r, 0)
        }
        link_id = _new_id("PMEL", existing)
        row = self._pm_links_table.rowCount()
        self._pm_links_table.insertRow(row)
        self._pm_links_table.setItem(row, 0, QTableWidgetItem(link_id))
        self._pm_links_table.setItem(row, 1, QTableWidgetItem(pm_id))
        self._pm_links_table.setItem(row, 2, QTableWidgetItem(""))
        self._pm_links_table.setItem(row, 3, QTableWidgetItem("1.0"))
        self._pm_links_table.setItem(row, 4, QTableWidgetItem(""))

    def _add_pm_task_row(self) -> None:
        existing = {
            self._pm_tasks_table.item(r, 0).text().strip()
            for r in range(self._pm_tasks_table.rowCount())
            if self._pm_tasks_table.item(r, 0)
        }
        pm_id = _new_id("PM", existing)
        row = self._pm_tasks_table.rowCount()
        self._pm_tasks_table.insertRow(row)
        self._pm_tasks_table.setItem(row, 0, QTableWidgetItem(pm_id))
        self._pm_tasks_table.setItem(row, 1, QTableWidgetItem("IN"))
        self._pm_tasks_table.setItem(row, 2, QTableWidgetItem(""))
        self._pm_tasks_table.setItem(row, 3, QTableWidgetItem("1.0"))
        self._pm_tasks_table.setItem(row, 4, QTableWidgetItem("0.0"))
        self._pm_tasks_table.setItem(row, 5, QTableWidgetItem(""))

    def _remove_selected_rows(self, table: QTableWidget) -> None:
        rows = sorted({idx.row() for idx in table.selectedIndexes()}, reverse=True)
        for r in rows:
            table.removeRow(r)

    def _selected_pm_id(self) -> str:
        rows = self._pm_tasks_table.selectedIndexes()
        if not rows:
            return ""
        r = rows[0].row()
        item = self._pm_tasks_table.item(r, 0)
        return item.text().strip() if item else ""

    def _on_mttf_changed(self, new_mttf: float) -> None:
        sigma = self._sigma.value()
        if not is_sigma_manual(self._last_mttf, sigma):
            self._sigma.blockSignals(True)
            self._sigma.setValue(coupled_sigma(new_mttf))
            self._sigma.blockSignals(False)
        self._last_mttf = float(new_mttf)

    def _on_pm_table_changed(self, _item: QTableWidgetItem) -> None:
        self._refresh_consistency_warnings()

    def _refresh_consistency_warnings(self) -> None:
        if not hasattr(self, "_basis_warn"):
            return
        current = copy.deepcopy(self._session.session.get("edit_current", {}))
        faal_rows = list(current.get("faalwijzes", []))
        pm_rows = list(current.get("pm_tasks", []))
        target = self._fm_id
        for row in faal_rows:
            if str(row.get("fm_id")) == target:
                row["failure_type"] = str(self._failure_type.currentData())
                break
        pm_raw = self._read_table(
            self._pm_tasks_table,
            ("pm_id", "taak_type", "taak_omschrijving", "interval_jaar", "cost_eur", "task_group_id"),
        )
        pm_by_id = {str(r["pm_id"]): r for r in pm_raw}
        updated_pm: list[dict[str, Any]] = []
        for row in pm_rows:
            if str(row.get("fm_id")) != target:
                updated_pm.append(row)
                continue
            patch = pm_by_id.get(str(row.get("pm_id")), {})
            merged = dict(row)
            if patch:
                merged.update(patch)
                merged["task_group_id"] = normalize_optional_fk(patch.get("task_group_id"))
            updated_pm.append(merged)
        for pm_id, patch in pm_by_id.items():
            if not any(str(r.get("pm_id")) == pm_id for r in updated_pm):
                updated_pm.append({**patch, "fm_id": target})
        other_pm = [r for r in pm_rows if str(r.get("fm_id")) != target]
        findings = findings_for_edit_rows(
            target,
            faal_rows,
            other_pm + updated_pm,
        )
        basis_msgs = [f.message_nl for f in findings if f.tab_hint == "basis"]
        prev_msgs = [f.message_nl for f in findings if f.tab_hint == "preventief"]
        self._basis_warn.setText("\n".join(basis_msgs))
        if hasattr(self, "_preventief_warn"):
            self._preventief_warn.setText("\n".join(prev_msgs))

    def _on_pm_task_selected(self) -> None:
        pm_id = self._selected_pm_id()
        group_id = ""
        for r in range(self._pm_tasks_table.rowCount()):
            if self._pm_tasks_table.item(r, 0) and self._pm_tasks_table.item(r, 0).text().strip() == pm_id:
                gitem = self._pm_tasks_table.item(r, 5)
                group_id = gitem.text().strip() if gitem else ""
                if group_id == messages.FM_EDITOR_TASK_GROUP_NONE:
                    group_id = ""
                break
        self._tg_group_id.setText(group_id)
        if group_id and group_id in self._task_group_rows:
            g = self._task_group_rows[group_id]
            self._tg_interval.setValue(float(g.get("interval_jaar") or 1.0))
            self._tg_cost.setValue(float(g.get("cost_eur") or 0.0))
            shared = count_faalwijzen_for_task_group_in_edit(self._session, group_id)
            if shared > 1:
                self._tg_warn.setText(
                    messages.FM_EDITOR_TASK_GROUP_SHARED_WARN.format(group_id=group_id)
                )
            else:
                self._tg_warn.setText("")
        else:
            self._tg_warn.setText("")

    def _build_draft(self) -> FmEditDraft:
        fm_links = self._read_table(
            self._fm_links_table, ("link_id", "klasse_id", "fractie", "aanname_fractie")
        )
        for row in fm_links:
            row["fm_id"] = self._fm_id

        pm_tasks_raw = self._read_table(
            self._pm_tasks_table,
            ("pm_id", "taak_type", "taak_omschrijving", "interval_jaar", "cost_eur", "task_group_id"),
        )
        orig_pm = {str(r.get("pm_id")): dict(r) for r in self._bundle.pm_task_rows}
        pm_tasks: list[dict[str, Any]] = []
        for row in pm_tasks_raw:
            base = copy.deepcopy(orig_pm.get(str(row["pm_id"]), {}))
            base.update(
                {
                    "pm_id": row["pm_id"],
                    "fm_id": self._fm_id,
                    "taak_type": row["taak_type"],
                    "taak_omschrijving": row["taak_omschrijving"],
                    "interval_jaar": row["interval_jaar"],
                    "cost_eur": row["cost_eur"],
                    "task_group_id": row["task_group_id"] or None,
                }
            )
            if "duration" not in base:
                base["duration"] = {"value": 0.0, "unit": "uur"}
            pm_tasks.append(base)

        pm_links = self._read_table(
            self._pm_links_table,
            ("link_id", "pm_id", "klasse_id", "fractie", "aanname_fractie"),
        )

        effect_rows = self._read_table(
            self._effect_table,
            ("klasse_id", "omschrijving", "categorie", "cost_gevolg_eur"),
        )
        for row in effect_rows:
            orig = next(
                (e for e in self._bundle.effect_klasse_rows if e.get("klasse_id") == row["klasse_id"]),
                {},
            )
            row["functie_id"] = orig.get("functie_id", "")
            row["notes"] = orig.get("notes", "")
            row["aanname_gevolg_kosten"] = orig.get("aanname_gevolg_kosten", "")

        task_groups = list(self._task_group_rows.values())
        gid = self._tg_group_id.text().strip()
        if gid and gid in self._task_group_rows:
            g = copy.deepcopy(self._task_group_rows[gid])
            g["interval_jaar"] = self._tg_interval.value()
            g["cost_eur"] = self._tg_cost.value()
            task_groups = [
                g if str(x.get("group_id")) == gid else x for x in task_groups
            ]

        return FmEditDraft(
            fm_id=self._fm_id,
            baseline=self._bundle,
            failure_type=str(self._failure_type.currentData()),
            aging_distribution=str(self._aging_distribution.currentData()),
            mttf_jaar=self._mttf.value(),
            sigma_jaar=self._sigma.value(),
            beta_jaar=self._beta.value(),
            is_evident=not self._nmf.isChecked(),
            faalwijze_omschrijving=self._omschrijving.text().strip(),
            functie_id=str(self._functie.currentData() or ""),
            repair_quality=self._repair_quality.value(),
            cm_materiaal=self._cm_materiaal.value(),
            cm_arbeid=self._cm_arbeid.value(),
            downtime_hours=self._downtime_hr.value(),
            notes=self._notes.toPlainText().strip(),
            aanname_cm_kosten=self._aanname_cm.text().strip(),
            aanname_downtime=self._aanname_downtime.text().strip(),
            bouwjaar=self._bouwjaar.value(),
            fm_effect_rows=tuple(fm_links),
            pm_task_rows=tuple(pm_tasks),
            pm_effect_rows=tuple(pm_links),
            effect_klasse_rows=tuple(effect_rows),
            task_group_rows=tuple(task_groups),
        )

    def _on_accept(self) -> None:
        bundle = assemble_bundle(self._build_draft())
        if self._path is None:
            result = commit_fm_edit(
                self._session,
                bundle,
                path=None,
                save_to_disk=False,
                baseline_mtime_ns=self._baseline_mtime_ns,
                run_policy=RunPolicy.BLOCKING,
            )
            self._finish_commit(result)
            return
        self._progress = QProgressDialog(messages.FM_EDITOR_COMMIT_BUSY, "", 0, 0, self)
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setCancelButton(None)
        self._progress.show()
        replace_before_async = bundle
        started = self._commit_runner.start(
            self._session,
            bundle=replace_before_async,
            project_path=self._path,
            save_to_disk=self._save_to_disk,
            baseline_mtime_ns=self._baseline_mtime_ns,
        )
        if not started:
            self._progress.close()
            result = commit_fm_edit(
                self._session,
                bundle,
                path=self._path,
                save_to_disk=self._save_to_disk,
                baseline_mtime_ns=self._baseline_mtime_ns,
                run_policy=RunPolicy.BLOCKING,
            )
            self._finish_commit(result)

    def _on_commit_finished(self, result: object) -> None:
        if self._progress is not None:
            self._progress.close()
            self._progress = None
        if isinstance(result, FmEditCommitResult):
            self._finish_commit(result)

    def _finish_commit(self, result: FmEditCommitResult) -> None:
        if not result.ok:
            detail = "\n".join(result.errors) if result.errors else "Onbekende fout"
            QMessageBox.warning(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.FM_EDITOR_COMMIT_FAILED.format(detail=detail),
            )
            return
        self.commit_result = result
        self.accept()
