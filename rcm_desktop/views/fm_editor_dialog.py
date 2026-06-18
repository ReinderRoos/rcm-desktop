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
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
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
from rcm_desktop.adapter.fm_create_service import validate_fm_minimum
from rcm_desktop.adapter.fm_editor_results_view_service import build_editor_results_view
from rcm_desktop.adapter.fm_field_copy_service import (
    copy_effect_scope,
    copy_fields,
    copy_preventief_scope,
)
from rcm_desktop.adapter.fm_library_fill_service import (
    apply_effect_klassen_from_library,
    apply_rev_tasks_from_library,
    effect_klasse_library_choices,
    rev_task_library_choices,
)
from rcm_desktop.adapter.pm_measure_link_service import apply_task_group_link
from rcm_desktop.adapter.task_group_catalog_service import (
    allocate_task_group_id,
    list_task_groups,
)
from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope, seed_create_bundle
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


class _FmEditorTabBarProxy:
    """QTabBar-compat voor sidebar-navigatie (tests + scroll-gedrag)."""

    def __init__(self, nav: QListWidget) -> None:
        self._nav = nav

    def usesScrollButtons(self) -> bool:
        return False

    def isVisible(self) -> bool:
        return self._nav.isVisible()

    def tabRect(self, index: int):
        item = self._nav.item(index)
        if item is None:
            return self._nav.visualRect(self._nav.indexAt(0, 0))
        return self._nav.visualItemRect(item)


class _FmEditorSectionTabs:
    """Verticale sectienavigatie i.p.v. horizontale QTabWidget-tabstrip."""

    def __init__(self, nav: QListWidget, stack: QStackedWidget) -> None:
        self._nav = nav
        self._stack = stack
        self._tab_bar = _FmEditorTabBarProxy(nav)
        nav.currentRowChanged.connect(self._stack.setCurrentIndex)

    def tabBar(self) -> _FmEditorTabBarProxy:
        return self._tab_bar

    def count(self) -> int:
        return self._stack.count()

    def tabText(self, index: int) -> str:
        item = self._nav.item(index)
        return item.text() if item is not None else ""

    def setCurrentIndex(self, index: int) -> None:
        self._nav.setCurrentRow(index)

    def currentIndex(self) -> int:
        return self._stack.currentIndex()

    def addTab(self, widget: QWidget, label: str) -> int:
        self._nav.addItem(label)
        self._stack.addWidget(widget)
        return self._stack.count() - 1


class FmEditorDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        project,
        fm_id: str | None = None,
        create_pbs_id: str | None = None,
        project_path: str | Path | None = None,
        save_to_disk: bool = False,
        baseline_mtime_ns: int | None = None,
        editing_session: EditingSession | None = None,
    ) -> None:
        super().__init__(parent)
        self._project = project
        self._create_mode = create_pbs_id is not None
        self._path = Path(project_path) if project_path else None
        self._save_to_disk = save_to_disk
        self._baseline_mtime_ns = baseline_mtime_ns
        if editing_session is not None:
            self._session = editing_session
        else:
            self._session = create_edit_session(project)
        if self._create_mode:
            if create_pbs_id is None:
                raise ValueError("create_pbs_id is verplicht in create-modus")
            self._bundle = seed_create_bundle(self._session, create_pbs_id)
            self._fm_id = self._bundle.fm_id
        else:
            if fm_id is None:
                raise ValueError("fm_id is verplicht buiten create-modus")
            self._fm_id = fm_id
            self._bundle = load_fm_edit_scope(self._session, fm_id)
        self.commit_result: FmEditCommitResult | None = None
        self._commit_runner = FmEditCommitRunner()
        self._commit_runner.finished.connect(self._on_commit_finished)
        self._progress: QProgressDialog | None = None
        self._functie_ids = tuple(sorted(project.functies.keys()))

        self.setWindowTitle(
            messages.FM_EDITOR_TITLE_CREATE.format(fm_id=self._fm_id)
            if self._create_mode
            else messages.FM_EDITOR_TITLE.format(fm_id=self._fm_id)
        )
        self.setMinimumSize(720, 600)

        root = QVBoxLayout(self)
        intro = QLabel(
            f"{self._bundle.faalwijze_row.get('faalwijze_omschrijving', '')} — "
            f"PBS {self._bundle.pbs_row.get('bouwdeel_naam', self._bundle.pbs_row.get('pbs_id', ''))}"
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        section_nav = QListWidget()
        section_nav.setFixedWidth(168)
        section_nav.setSpacing(2)
        section_nav.setObjectName("FmEditorSectionNav")
        section_stack = QStackedWidget()
        section_stack.setMinimumHeight(400)
        section_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._tabs = _FmEditorSectionTabs(section_nav, section_stack)
        self._tabs.addTab(self._build_basis_tab(), messages.FM_EDITOR_TAB_BASIS)
        self._tabs.addTab(
            self._wrap_scroll_tab(self._build_effecten_tab()),
            messages.FM_EDITOR_TAB_EFFECTEN,
        )
        self._tabs.addTab(self._build_correctief_tab(), messages.FM_EDITOR_TAB_CORRECTIEF)
        self._tabs.addTab(
            self._wrap_scroll_tab(self._build_preventief_tab()),
            messages.FM_EDITOR_TAB_PREVENTIEF,
        )
        self._results_tab_index = self._tabs.addTab(
            self._build_results_tab(), messages.FM_EDITOR_TAB_RESULTATEN
        )
        section_row = QHBoxLayout()
        section_row.setSpacing(8)
        section_row.addWidget(section_nav)
        section_row.addWidget(section_stack, stretch=1)
        root.addLayout(section_row, stretch=1)

        self._dirty = False
        self._stay_open_after_commit = False
        button_row = QHBoxLayout()
        self._save_btn = QPushButton(messages.FM_EDITOR_SAVE)
        self._save_close_btn = QPushButton(messages.FM_EDITOR_SAVE_AND_CLOSE)
        self._cancel_btn = QPushButton("Annuleren")
        self._save_btn.clicked.connect(lambda: self._commit(stay_open=True))
        self._save_close_btn.clicked.connect(lambda: self._commit(stay_open=False))
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_row.addStretch(1)
        button_row.addWidget(self._save_btn)
        button_row.addWidget(self._save_close_btn)
        button_row.addWidget(self._cancel_btn)
        root.addLayout(button_row)
        self.resize(860, 680)
        self._wire_dirty_tracking()
        self._update_results_tab()

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
        pbs_label = QLabel(
            f"{pbs_id} — {self._bundle.pbs_row.get('bouwdeel_naam', '')}"
        )
        pbs_label.setWordWrap(True)
        if self._create_mode:
            form.addRow(messages.FM_EDITOR_PBS_FIXED, pbs_label)
        shared = count_faalwijzen_for_pbs_in_edit(self._session, pbs_id)
        if shared > 1:
            warn = QLabel(
                messages.FM_EDITOR_PBS_SHARED_WARN.format(pbs_id=pbs_id, count=shared)
            )
            warn.setWordWrap(True)
            warn.setStyleSheet("color: #E65100;")
            form.addRow(warn)

        fill_row = QHBoxLayout()
        fill_basis = QPushButton(messages.FM_EDITOR_FILL_FROM)
        fill_basis.clicked.connect(self._on_fill_from_basis)
        fill_row.addWidget(fill_basis)
        fill_row.addStretch(1)
        form.addRow(fill_row)

        self._refresh_aging_fields_visibility()
        return page

    def _wire_dirty_tracking(self) -> None:
        def _mark_dirty(*_args: object) -> None:
            self._dirty = True

        for widget in (
            self._failure_type,
            self._mttf,
            self._sigma,
            self._aging_distribution,
            self._beta,
            self._nmf,
            self._omschrijving,
            self._functie,
            self._repair_quality,
            self._bouwjaar,
            self._cm_materiaal,
            self._cm_arbeid,
            self._downtime_hr,
            self._aanname_cm,
            self._aanname_downtime,
        ):
            if hasattr(widget, "valueChanged"):
                widget.valueChanged.connect(_mark_dirty)  # type: ignore[union-attr]
            elif hasattr(widget, "currentIndexChanged"):
                widget.currentIndexChanged.connect(_mark_dirty)  # type: ignore[union-attr]
            elif hasattr(widget, "textChanged"):
                widget.textChanged.connect(_mark_dirty)  # type: ignore[union-attr]
            elif hasattr(widget, "stateChanged"):
                widget.stateChanged.connect(_mark_dirty)  # type: ignore[union-attr]
        self._notes.textChanged.connect(_mark_dirty)
        for table in (
            self._fm_links_table,
            self._pm_links_table,
            self._effect_table,
            self._pm_tasks_table,
        ):
            table.itemChanged.connect(_mark_dirty)

    def _reload_editor_from_session(self) -> None:
        self._bundle = load_fm_edit_scope(self._session, self._fm_id)
        self._create_mode = False
        self._dirty = False
        row = self._bundle.faalwijze_row
        ft = str(row.get("failure_type", "random"))
        idx = self._failure_type.findData(ft)
        self._failure_type.setCurrentIndex(max(0, idx))
        self._mttf.setValue(float(row.get("mttf_jaar") or 1.0))
        self._sigma.setValue(float(row.get("sigma_jaar") or 0.0))
        cur_dist = str(row.get("aging_distribution") or "normal")
        dist_idx = self._aging_distribution.findData(cur_dist)
        self._aging_distribution.setCurrentIndex(max(0, dist_idx))
        self._beta.setValue(float(row.get("beta_jaar") or 0.0))
        self._nmf.setChecked(not bool(row.get("is_evident", True)))
        self._omschrijving.setText(str(row.get("faalwijze_omschrijving") or ""))
        cur_f = str(row.get("functie_id") or "")
        fi = self._functie.findData(cur_f)
        if fi >= 0:
            self._functie.setCurrentIndex(fi)
        self._repair_quality.setValue(float(row.get("repair_quality") or 1.0))
        self._bouwjaar.setValue(int(self._bundle.pbs_row.get("bouwjaar") or 0))
        split = split_cm_cost(
            float(row.get("cost_cm_eur") or 0.0),
            hint=str(row.get("aanname_cm_kosten") or ""),
        )
        self._cm_materiaal.setValue(split.materiaal_eur)
        self._cm_arbeid.setValue(split.arbeid_eur)
        self._downtime_hr.setValue(downtime_hours_from_row(row))
        self._notes.setPlainText(str(row.get("notes") or ""))
        self._aanname_cm.setText(str(row.get("aanname_cm_kosten") or ""))
        self._aanname_downtime.setText(str(row.get("aanname_downtime") or ""))
        fm_cols = ("link_id", "klasse_id", "fractie", "aanname_fractie")
        self._fill_table(self._fm_links_table, list(self._bundle.fm_effect_rows), fm_cols)
        pm_link_cols = ("link_id", "pm_id", "klasse_id", "fractie", "aanname_fractie")
        self._fill_table(self._pm_links_table, list(self._bundle.pm_effect_rows), pm_link_cols)
        ek_cols = ("klasse_id", "omschrijving", "categorie", "cost_gevolg_eur")
        self._fill_table(self._effect_table, list(self._bundle.effect_klasse_rows), ek_cols)
        self._task_group_rows = {
            str(r.get("group_id")): dict(r) for r in self._bundle.task_group_rows
        }
        pm_cols = (
            "pm_id",
            "taak_type",
            "taak_omschrijving",
            "interval_jaar",
            "cost_eur",
            "task_group_id",
        )
        pm_rows = []
        for pm_row in self._bundle.pm_task_rows:
            flat = dict(pm_row)
            flat["taak_type"] = (
                flat.get("taak_type", {}).get("value")
                if isinstance(flat.get("taak_type"), dict)
                else flat.get("taak_type", "")
            )
            pm_rows.append(flat)
        self._fill_table(self._pm_tasks_table, pm_rows, pm_cols)
        tg_ids = tuple(sorted(self._task_group_rows.keys()))
        self._pm_tasks_table.setItemDelegateForColumn(
            5, PmTaskGroupDelegate(tg_ids, self._pm_tasks_table)
        )
        self._refresh_aging_fields_visibility()
        self._refresh_consistency_warnings()
        self._refresh_results_tab()
        self._dirty = False

    def _refresh_results_tab(self) -> None:
        if self._results_tab_index is None:
            return
        refresh = getattr(self, "_results_tab_refresh", None)
        if callable(refresh):
            refresh()

    def _on_cancel(self) -> None:
        if self._dirty:
            answer = QMessageBox.question(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.FM_EDITOR_CANCEL_DIRTY,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.reject()

    def _set_commit_buttons_enabled(self, enabled: bool) -> None:
        self._save_btn.setEnabled(enabled)
        self._save_close_btn.setEnabled(enabled)

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

    def _wrap_scroll_tab(self, page: QWidget) -> QScrollArea:
        page.setMinimumHeight(300)
        page.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(page)
        scroll.setMinimumHeight(300)
        scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        return scroll

    def _make_table(self, headers: tuple[str, ...]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(list(headers))
        table.horizontalHeader().setStretchLastSection(True)
        table.setMinimumHeight(80)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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

        fill_row = QHBoxLayout()
        fill_effecten = QPushButton(messages.FM_EDITOR_FILL_FROM_EFFECTEN)
        fill_effecten.clicked.connect(self._on_fill_from_effecten)
        fill_row.addWidget(fill_effecten)
        fill_row.addStretch(1)
        layout.addLayout(fill_row)

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
        layout.addWidget(self._fm_links_table, stretch=1)
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
        layout.addWidget(self._pm_links_table, stretch=1)
        layout.addLayout(pm_btns)

        ek_cols = ("klasse_id", "omschrijving", "categorie", "cost_gevolg_eur")
        layout.addWidget(QLabel(messages.FM_EDITOR_EFFECT_KLASSEN))
        self._effect_table = self._make_table(ek_cols)
        self._fill_table(self._effect_table, list(self._bundle.effect_klasse_rows), ek_cols)
        layout.addWidget(self._effect_table, stretch=1)
        return page

    def _build_preventief_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        fill_row = QHBoxLayout()
        fill_preventief = QPushButton(messages.FM_EDITOR_FILL_FROM_PREVENTIEF)
        fill_preventief.clicked.connect(self._on_fill_from_preventief)
        fill_row.addWidget(fill_preventief)
        fill_row.addStretch(1)
        layout.addLayout(fill_row)

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
        link_pm = QPushButton(messages.FM_EDITOR_LINK_MEASURE)
        link_pm.clicked.connect(self._on_link_measure)
        new_tg = QPushButton(messages.FM_EDITOR_NEW_TASK_GROUP)
        new_tg.clicked.connect(self._on_new_task_group)
        pm_btns.addWidget(link_pm)
        pm_btns.addWidget(new_tg)
        pm_btns.addStretch(1)
        layout.addWidget(self._pm_tasks_table, stretch=1)
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

    def _build_results_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self._results_summary = QLabel(messages.FM_EDITOR_RESULTS_EMPTY)
        self._results_summary.setWordWrap(True)
        layout.addWidget(self._results_summary)
        self._results_type_counts = QLabel("")
        self._results_type_counts.setWordWrap(True)
        layout.addWidget(self._results_type_counts)
        self._results_pm_table = QTableWidget(0, 5)
        self._results_pm_table.setHorizontalHeaderLabels(
            ["PM", "Type", "Interval (jr)", "Taakgroep", "Eerste uitvoeringsjaar"]
        )
        self._results_pm_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._results_pm_table, stretch=1)
        self._results_tab_refresh = self._update_results_tab
        return page

    def _update_results_tab(self) -> None:
        project = self._project
        fmr = None
        if self.commit_result is not None and self.commit_result.project is not None:
            project = self.commit_result.project
        if self.commit_result is not None and self.commit_result.run_result is not None:
            for item in self.commit_result.run_result.fm_core_results:
                if str(item.fm_id) == self._fm_id:
                    fmr = item
                    break
        view = build_editor_results_view(project, self._fm_id, fmr)
        if not view.has_results:
            self._results_summary.setText(messages.FM_EDITOR_RESULTS_EMPTY)
            self._results_type_counts.setText("")
        else:
            self._results_summary.setText(
                f"Verwacht aantal falen: {view.expected_failures:.2f}\n"
                f"Totale niet-beschikbaarheid (uur): {view.total_downtime_hr:.1f}\n"
                f"CM-kosten (EUR): {view.cm_cost_eur:,.0f} | PM-kosten (EUR): {view.pm_cost_eur:,.0f} | "
                f"Totaal (EUR): {view.total_cost_eur:,.0f}"
            )
            counts = ", ".join(f"{tt}: {n}" for tt, n in view.pm_type_counts)
            self._results_type_counts.setText(f"PM-tellingen — {counts}" if counts else "")
        self._results_pm_table.setRowCount(len(view.pm_rows))
        for row_idx, pm_row in enumerate(view.pm_rows):
            first_year = (
                str(pm_row.first_execution_calendar_year)
                if pm_row.first_execution_calendar_year is not None
                else "—"
            )
            for col_idx, val in enumerate(
                (
                    pm_row.pm_id,
                    pm_row.taak_type,
                    f"{pm_row.interval_jaar:.2f}",
                    pm_row.task_group_id or "—",
                    first_year,
                )
            ):
                self._results_pm_table.setItem(row_idx, col_idx, QTableWidgetItem(val))

    def _apply_faalwijze_row_to_basis_correctief(self, row: dict[str, Any]) -> None:
        ft = str(row.get("failure_type", "random"))
        idx = self._failure_type.findData(ft)
        self._failure_type.setCurrentIndex(max(0, idx))
        self._mttf.setValue(float(row.get("mttf_jaar") or 1.0))
        self._sigma.setValue(float(row.get("sigma_jaar") or 0.0))
        cur_dist = str(row.get("aging_distribution") or "normal")
        dist_idx = self._aging_distribution.findData(cur_dist)
        self._aging_distribution.setCurrentIndex(max(0, dist_idx))
        self._beta.setValue(float(row.get("beta_jaar") or 0.0))
        self._nmf.setChecked(not bool(row.get("is_evident", True)))
        self._omschrijving.setText(str(row.get("faalwijze_omschrijving") or ""))
        cur_f = str(row.get("functie_id") or "")
        fi = self._functie.findData(cur_f)
        if fi >= 0:
            self._functie.setCurrentIndex(fi)
        self._repair_quality.setValue(float(row.get("repair_quality") or 1.0))
        split = split_cm_cost(
            float(row.get("cost_cm_eur") or 0.0),
            hint=str(row.get("aanname_cm_kosten") or ""),
        )
        self._cm_materiaal.setValue(split.materiaal_eur)
        self._cm_arbeid.setValue(split.arbeid_eur)
        self._downtime_hr.setValue(downtime_hours_from_row(row))
        self._notes.setPlainText(str(row.get("notes") or ""))
        self._aanname_cm.setText(str(row.get("aanname_cm_kosten") or ""))
        self._aanname_downtime.setText(str(row.get("aanname_downtime") or ""))
        self._refresh_aging_fields_visibility()

    def _pick_source_fm_id(
        self,
        *,
        title: str | None = None,
        picker_label: str | None = None,
        scope: str = "basis",
    ) -> str | None:
        rows = self._session.session.get("edit_current", {}).get("faalwijzes", [])
        current = self._session.session.get("edit_current", {})
        choices: list[str] = []
        id_by_label: dict[str, str] = {}
        for row in rows:
            fm_id = str(row.get("fm_id") or "")
            if fm_id == self._fm_id:
                continue
            omschrijving = str(row.get("faalwijze_omschrijving") or "")
            if scope == "effecten":
                effect_count = sum(
                    1
                    for link in current.get("fm_effect_links", [])
                    if str(link.get("fm_id") or "") == fm_id
                ) + sum(
                    1
                    for link in current.get("pm_effect_links", [])
                    if str(link.get("pm_id") or "") in {
                        str(task.get("pm_id") or "")
                        for task in current.get("pm_tasks", [])
                        if str(task.get("fm_id") or "") == fm_id
                    }
                )
                label = messages.FM_EDITOR_FILL_FROM_CHOICE_EFFECTEN.format(
                    fm_id=fm_id,
                    omschrijving=omschrijving,
                    effect_count=effect_count,
                )
            elif scope == "preventief":
                pm_count = sum(
                    1
                    for task in current.get("pm_tasks", [])
                    if str(task.get("fm_id") or "") == fm_id
                )
                label = messages.FM_EDITOR_FILL_FROM_CHOICE_PREVENTIEF.format(
                    fm_id=fm_id,
                    omschrijving=omschrijving,
                    pm_count=pm_count,
                )
            else:
                label = f"{fm_id} — {omschrijving}"
            choices.append(label)
            id_by_label[label] = fm_id
        if not choices:
            return None
        default_picker = messages.FM_EDITOR_FILL_FROM_PICKER_FM
        if scope == "effecten":
            default_picker = messages.FM_EDITOR_FILL_FROM_PICKER_FM_EFFECTEN
        elif scope == "preventief":
            default_picker = messages.FM_EDITOR_FILL_FROM_PICKER_FM_PREVENTIEF
        picked, ok = QInputDialog.getItem(
            self,
            title or messages.FM_EDITOR_FILL_FROM_TITLE,
            picker_label or default_picker,
            choices,
            0,
            False,
        )
        if not ok or not picked:
            return None
        return id_by_label[picked]

    def _pick_library_ids(
        self,
        *,
        choices: list[tuple[str, str]],
        title: str,
        label: str,
    ) -> list[str]:
        if not choices:
            return []
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(label))
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        id_by_row: list[str] = []
        for choice_label, item_id in choices:
            list_widget.addItem(choice_label)
            id_by_row.append(item_id)
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return []
        selected: list[str] = []
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            if item is not None and item.isSelected():
                selected.append(id_by_row[row])
        return selected

    def _confirm_fill_overwrite(self, *, title: str, message: str) -> bool:
        if not self._dirty:
            return True
        answer = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _on_fill_from_basis(self) -> None:
        source_fm_id = self._pick_source_fm_id()
        if source_fm_id is None:
            return
        if not self._confirm_fill_overwrite(
            title=messages.FM_EDITOR_FILL_FROM_TITLE,
            message=messages.FM_EDITOR_FILL_FROM_CONFIRM.format(fm_id=source_fm_id),
        ):
            return
        rows = self._session.session.get("edit_current", {}).get("faalwijzes", [])
        source_row = next(r for r in rows if str(r.get("fm_id")) == source_fm_id)
        merged = copy_fields(source_row, self._bundle.faalwijze_row)
        self._bundle = FmEditBundle(
            fm_id=self._bundle.fm_id,
            faalwijze_row=merged,
            pbs_row=self._bundle.pbs_row,
            fm_effect_rows=self._bundle.fm_effect_rows,
            pm_task_rows=self._bundle.pm_task_rows,
            pm_effect_rows=self._bundle.pm_effect_rows,
            task_group_rows=self._bundle.task_group_rows,
            effect_klasse_rows=self._bundle.effect_klasse_rows,
        )
        self._apply_faalwijze_row_to_basis_correctief(merged)
        self._dirty = True

    def _on_fill_from_effecten(self) -> None:
        edit_current = self._session.session.get("edit_current", {})
        choices = effect_klasse_library_choices(edit_current)
        selected_ids = self._pick_library_ids(
            choices=choices,
            title=messages.FM_EDITOR_FILL_FROM_EFFECTEN_TITLE,
            label=messages.FM_EDITOR_FILL_FROM_PICKER_EFFECT_KLASSEN,
        )
        if not selected_ids:
            return
        if not self._confirm_fill_overwrite(
            title=messages.FM_EDITOR_FILL_FROM_EFFECTEN_TITLE,
            message=messages.FM_EDITOR_FILL_FROM_EFFECTEN_CONFIRM.format(
                effect_count=len(selected_ids),
            ),
        ):
            return
        existing_links = {
            str(r.get("link_id"))
            for r in self._bundle.fm_effect_rows + self._bundle.pm_effect_rows
            if r.get("link_id")
        }
        copied = apply_effect_klassen_from_library(
            edit_current,
            target_fm_id=self._fm_id,
            selected_klasse_ids=tuple(selected_ids),
            existing_link_ids=existing_links,
        )
        merged_klassen = list(self._bundle.effect_klasse_rows)
        seen = {str(r.get("klasse_id")) for r in merged_klassen if r.get("klasse_id")}
        for row in copied.effect_klasse_rows:
            kid = str(row.get("klasse_id") or "")
            if kid and kid not in seen:
                merged_klassen.append(row)
                seen.add(kid)
        self._bundle = FmEditBundle(
            fm_id=self._bundle.fm_id,
            faalwijze_row=self._bundle.faalwijze_row,
            pbs_row=self._bundle.pbs_row,
            fm_effect_rows=copied.fm_effect_rows,
            pm_task_rows=self._bundle.pm_task_rows,
            pm_effect_rows=copied.pm_effect_rows,
            task_group_rows=self._bundle.task_group_rows,
            effect_klasse_rows=tuple(merged_klassen),
        )
        fm_cols = ("link_id", "klasse_id", "fractie", "aanname_fractie")
        self._fill_table(self._fm_links_table, list(copied.fm_effect_rows), fm_cols)
        pm_cols = ("link_id", "pm_id", "klasse_id", "fractie", "aanname_fractie")
        self._fill_table(self._pm_links_table, list(copied.pm_effect_rows), pm_cols)
        ek_cols = ("klasse_id", "omschrijving", "categorie", "cost_gevolg_eur")
        self._fill_table(self._effect_table, list(merged_klassen), ek_cols)
        self._dirty = True

    def _on_fill_from_preventief(self) -> None:
        edit_current = self._session.session.get("edit_current", {})
        choices = rev_task_library_choices(edit_current)
        selected_ids = self._pick_library_ids(
            choices=choices,
            title=messages.FM_EDITOR_FILL_FROM_PREVENTIEF_TITLE,
            label=messages.FM_EDITOR_FILL_FROM_PICKER_REV_TAKEN,
        )
        if not selected_ids:
            return
        if not self._confirm_fill_overwrite(
            title=messages.FM_EDITOR_FILL_FROM_PREVENTIEF_TITLE,
            message=messages.FM_EDITOR_FILL_FROM_PREVENTIEF_CONFIRM.format(
                pm_count=len(selected_ids),
            ),
        ):
            return
        session_pm_ids = {
            str(r.get("pm_id"))
            for r in edit_current.get("pm_tasks", [])
            if r.get("pm_id")
        }
        copied = apply_rev_tasks_from_library(
            edit_current,
            target_fm_id=self._fm_id,
            selected_pm_ids=tuple(selected_ids),
            existing_pm_ids=session_pm_ids,
        )
        self._bundle = FmEditBundle(
            fm_id=self._bundle.fm_id,
            faalwijze_row=self._bundle.faalwijze_row,
            pbs_row=self._bundle.pbs_row,
            fm_effect_rows=self._bundle.fm_effect_rows,
            pm_task_rows=copied.pm_task_rows,
            pm_effect_rows=(),
            task_group_rows=(),
            effect_klasse_rows=self._bundle.effect_klasse_rows,
        )
        pm_cols = (
            "pm_id",
            "taak_type",
            "taak_omschrijving",
            "interval_jaar",
            "cost_eur",
            "task_group_id",
        )
        rows = []
        for row in copied.pm_task_rows:
            flat = dict(row)
            flat["taak_type"] = (
                flat.get("taak_type", {}).get("value")
                if isinstance(flat.get("taak_type"), dict)
                else flat.get("taak_type", "")
            )
            rows.append(flat)
        self._fill_table(self._pm_tasks_table, rows, pm_cols)
        self._task_group_rows = {}
        tg_ids: tuple[str, ...] = ()
        self._pm_tasks_table.setItemDelegateForColumn(
            5, PmTaskGroupDelegate(tg_ids, self._pm_tasks_table)
        )
        self._dirty = True

    def _on_link_measure(self) -> None:
        groups = list_task_groups(self._session)
        if not groups:
            return
        labels = [
            f"{g.group_id} — {g.omschrijving} ({len(g.fm_ids)} FM's)"
            for g in groups
        ]
        picked, ok = QInputDialog.getItem(
            self,
            messages.FM_EDITOR_LINK_MEASURE_TITLE,
            "Taakgroep",
            labels,
            0,
            False,
        )
        if not ok or not picked:
            return
        group_id = picked.split(" — ", 1)[0]
        row_idx = self._pm_tasks_table.currentRow()
        if row_idx < 0:
            return
        pm_cols = (
            "pm_id",
            "taak_type",
            "taak_omschrijving",
            "interval_jaar",
            "cost_eur",
            "task_group_id",
        )
        pm_rows = self._read_table(self._pm_tasks_table, pm_cols)
        if row_idx >= len(pm_rows):
            return
        linked = apply_task_group_link(pm_rows[row_idx], group_id, self._session)
        pm_rows[row_idx] = linked
        self._fill_table(self._pm_tasks_table, pm_rows, pm_cols)
        self._dirty = True

    def _on_new_task_group(self) -> None:
        group_id = allocate_task_group_id(self._session)
        interval, ok1 = QInputDialog.getDouble(
            self, messages.FM_EDITOR_NEW_TASK_GROUP_TITLE, "Interval (jaar)", 1.0, 0.01, 500.0, 2
        )
        if not ok1:
            return
        cost, ok2 = QInputDialog.getDouble(
            self, messages.FM_EDITOR_NEW_TASK_GROUP_TITLE, "Kosten (EUR)", 0.0, 0.0, 1e12, 2
        )
        if not ok2:
            return
        self._task_group_rows[group_id] = {
            "group_id": group_id,
            "omschrijving": "",
            "interval_jaar": interval,
            "cost_eur": cost,
            "causes_unavailability": False,
            "unavailability_fraction": 0.0,
            "duration": {"value": 0.0, "unit": "uur"},
        }
        row_idx = self._pm_tasks_table.currentRow()
        if row_idx >= 0:
            item = self._pm_tasks_table.item(row_idx, 5)
            if item is None:
                item = QTableWidgetItem(group_id)
                self._pm_tasks_table.setItem(row_idx, 5, item)
            else:
                item.setText(group_id)
        tg_ids = tuple(sorted(self._task_group_rows.keys()))
        self._pm_tasks_table.setItemDelegateForColumn(
            5, PmTaskGroupDelegate(tg_ids, self._pm_tasks_table)
        )
        self._dirty = True

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
        self._dirty = True

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
        self._dirty = True

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
        self._dirty = True

    def _remove_selected_rows(self, table: QTableWidget) -> None:
        rows = sorted({idx.row() for idx in table.selectedIndexes()}, reverse=True)
        for r in rows:
            table.removeRow(r)
        if rows:
            self._dirty = True

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
        self._dirty = True
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

    def _commit(self, *, stay_open: bool) -> None:
        if self._commit_runner.busy:
            return
        self._stay_open_after_commit = stay_open
        bundle = assemble_bundle(self._build_draft())
        row_errors = validate_fm_minimum(bundle.faalwijze_row)
        if row_errors:
            QMessageBox.warning(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.FM_EDITOR_COMMIT_FAILED.format(detail="\n".join(row_errors)),
            )
            return
        self._set_commit_buttons_enabled(False)
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
        started = self._commit_runner.start(
            self._session,
            bundle=bundle,
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
        self._set_commit_buttons_enabled(True)
        if not result.ok:
            detail = "\n".join(result.errors) if result.errors else "Onbekende fout"
            QMessageBox.warning(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.FM_EDITOR_COMMIT_FAILED.format(detail=detail),
            )
            return
        self.commit_result = result
        if self._stay_open_after_commit:
            self._reload_editor_from_session()
            self._update_results_tab()
            return
        self.accept()
