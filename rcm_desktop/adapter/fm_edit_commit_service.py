"""Orchestratie commit + incrementele run voor faalwijze-editor (Qt-vrij)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rcm_core.editing.state import blocking_edit_error_count
from rcm_core.editing.validation import normalize_key
from rcm_core.incremental_run import run_incremental_analysis
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.fm_edit_bundle_service import FmEditBundle
from rcm_desktop.adapter.adapter_error_handling import log_adapter_exception
from rcm_desktop.adapter.run_service import RunResult, build_run_result
from rcm_desktop.adapter.save_service import SaveConflictError, save_project_atomically


@dataclass(frozen=True)
class FmEditCommitResult:
    ok: bool
    errors: tuple[str, ...]
    affected_fm_ids: tuple[str, ...]
    project: RCMProject | None
    run_result: RunResult | None


def create_edit_session(project: RCMProject) -> EditingSession:
    return EditingSession().clone_with_project(project)


def fm_exists_in_edit_session(session: EditingSession, fm_id: str) -> bool:
    target = normalize_key(fm_id)
    rows = session.session.get("edit_current", {}).get("faalwijzes", [])
    return any(normalize_key(row.get("fm_id")) == target for row in rows)


def replace_fm_scope(session: EditingSession, bundle: FmEditBundle) -> None:
    """Vervang alleen rijen in FM-scope; overige projectrijen blijven intact."""
    fm_id = bundle.fm_id
    pbs_id = normalize_key(bundle.pbs_row.get("pbs_id"))

    all_faalwijzen = copy.deepcopy(session.session["edit_current"]["faalwijzes"])
    updated_faalwijzen = []
    for row in all_faalwijzen:
        if normalize_key(row.get("fm_id")) == fm_id:
            updated_faalwijzen.append(copy.deepcopy(bundle.faalwijze_row))
        else:
            updated_faalwijzen.append(row)
    session.apply_entity_rows("faalwijzes", updated_faalwijzen)

    all_pbs = copy.deepcopy(session.session["edit_current"]["pbs"])
    updated_pbs = []
    for row in all_pbs:
        if normalize_key(row.get("pbs_id")) == pbs_id:
            updated_pbs.append(copy.deepcopy(bundle.pbs_row))
        else:
            updated_pbs.append(row)
    session.apply_entity_rows("pbs", updated_pbs)

    all_fm_links = copy.deepcopy(session.session["edit_current"]["fm_effect_links"])
    merged_fm_links = [
        r for r in all_fm_links if normalize_key(r.get("fm_id")) != fm_id
    ]
    merged_fm_links.extend(copy.deepcopy(r) for r in bundle.fm_effect_rows)
    session.apply_entity_rows("fm_effect_links", merged_fm_links)

    pm_ids = {normalize_key(r.get("pm_id")) for r in bundle.pm_task_rows}
    all_pm = copy.deepcopy(session.session["edit_current"]["pm_tasks"])
    merged_pm = [r for r in all_pm if normalize_key(r.get("fm_id")) != fm_id]
    merged_pm.extend(copy.deepcopy(r) for r in bundle.pm_task_rows)
    session.apply_entity_rows("pm_tasks", merged_pm)

    all_pm_links = copy.deepcopy(session.session["edit_current"]["pm_effect_links"])
    merged_pm_links = [
        r for r in all_pm_links if normalize_key(r.get("pm_id")) not in pm_ids
    ]
    merged_pm_links.extend(copy.deepcopy(r) for r in bundle.pm_effect_rows)
    session.apply_entity_rows("pm_effect_links", merged_pm_links)

    group_ids = {normalize_key(r.get("group_id")) for r in bundle.task_group_rows}
    all_groups = copy.deepcopy(session.session["edit_current"]["task_groups"])
    merged_groups = [r for r in all_groups if normalize_key(r.get("group_id")) not in group_ids]
    merged_groups.extend(copy.deepcopy(r) for r in bundle.task_group_rows)
    session.apply_entity_rows("task_groups", merged_groups)

    klasse_ids = {normalize_key(r.get("klasse_id")) for r in bundle.effect_klasse_rows}
    all_ek = copy.deepcopy(session.session["edit_current"]["effect_klassen"])
    merged_ek = [r for r in all_ek if normalize_key(r.get("klasse_id")) not in klasse_ids]
    merged_ek.extend(copy.deepcopy(r) for r in bundle.effect_klasse_rows)
    session.apply_entity_rows("effect_klassen", merged_ek)


def insert_fm_scope(session: EditingSession, bundle: FmEditBundle) -> None:
    """Voeg nieuwe FM-scope toe; faalwijze-id mag nog niet in sessie staan."""
    fm_id = normalize_key(bundle.fm_id)
    if fm_exists_in_edit_session(session, fm_id):
        raise ValueError(f"Faalwijze bestaat al in sessie: {fm_id}")

    all_faalwijzen = copy.deepcopy(session.session["edit_current"]["faalwijzes"])
    all_faalwijzen.append(copy.deepcopy(bundle.faalwijze_row))
    session.apply_entity_rows("faalwijzes", all_faalwijzen)

    pbs_id = normalize_key(bundle.pbs_row.get("pbs_id"))
    all_pbs = copy.deepcopy(session.session["edit_current"]["pbs"])
    updated_pbs = []
    for row in all_pbs:
        if normalize_key(row.get("pbs_id")) == pbs_id:
            updated_pbs.append(copy.deepcopy(bundle.pbs_row))
        else:
            updated_pbs.append(row)
    session.apply_entity_rows("pbs", updated_pbs)

    if bundle.fm_effect_rows:
        all_fm_links = copy.deepcopy(session.session["edit_current"]["fm_effect_links"])
        all_fm_links.extend(copy.deepcopy(r) for r in bundle.fm_effect_rows)
        session.apply_entity_rows("fm_effect_links", all_fm_links)

    if bundle.pm_task_rows:
        all_pm = copy.deepcopy(session.session["edit_current"]["pm_tasks"])
        all_pm.extend(copy.deepcopy(r) for r in bundle.pm_task_rows)
        session.apply_entity_rows("pm_tasks", all_pm)

    if bundle.pm_effect_rows:
        all_pm_links = copy.deepcopy(session.session["edit_current"]["pm_effect_links"])
        all_pm_links.extend(copy.deepcopy(r) for r in bundle.pm_effect_rows)
        session.apply_entity_rows("pm_effect_links", all_pm_links)

    if bundle.task_group_rows:
        group_ids = {normalize_key(r.get("group_id")) for r in bundle.task_group_rows}
        all_groups = copy.deepcopy(session.session["edit_current"]["task_groups"])
        merged_groups = [
            r for r in all_groups if normalize_key(r.get("group_id")) not in group_ids
        ]
        merged_groups.extend(copy.deepcopy(r) for r in bundle.task_group_rows)
        session.apply_entity_rows("task_groups", merged_groups)

    if bundle.effect_klasse_rows:
        klasse_ids = {normalize_key(r.get("klasse_id")) for r in bundle.effect_klasse_rows}
        all_ek = copy.deepcopy(session.session["edit_current"]["effect_klassen"])
        merged_ek = [r for r in all_ek if normalize_key(r.get("klasse_id")) not in klasse_ids]
        merged_ek.extend(copy.deepcopy(r) for r in bundle.effect_klasse_rows)
        session.apply_entity_rows("effect_klassen", merged_ek)


def apply_fm_scope(session: EditingSession, bundle: FmEditBundle) -> None:
    """Insert of replace afhankelijk van aanwezigheid ``fm_id`` in sessie."""
    if fm_exists_in_edit_session(session, bundle.fm_id):
        replace_fm_scope(session, bundle)
    else:
        insert_fm_scope(session, bundle)


def apply_bundle_scope(session: EditingSession, bundle: FmEditBundle) -> None:
    """Compat-wrapper — gebruik ``apply_fm_scope``."""
    apply_fm_scope(session, bundle)


def _collect_error_messages(session: EditingSession) -> tuple[str, ...]:
    messages: list[str] = []
    for entity, rows_e in session.session.get("edit_errors", {}).items():
        for row_key, fields in rows_e.items():
            for field, errs in fields.items():
                for err in errs:
                    msg = err.get("message", "")
                    if msg:
                        messages.append(f"{entity} / {row_key} / {field}: {msg}")
    return tuple(messages)


def commit_edits(
    session: EditingSession,
    *,
    project_path: str | Path | None = None,
    save_to_disk: bool = False,
    baseline_mtime_ns: int | None = None,
) -> FmEditCommitResult:
    session.validate()
    if session.base_project is not None:
        from rcm_desktop.adapter.input_grid_findings import inject_input_grid_findings

        inject_input_grid_findings(session.session, base_project=session.base_project)
    if blocking_edit_error_count(session.session) > 0:
        err_msgs = _collect_error_messages(session)
        return FmEditCommitResult(
            ok=False,
            errors=err_msgs,
            affected_fm_ids=(),
            project=None,
            run_result=None,
        )

    built = session.build_project()
    path_obj = Path(project_path) if project_path else None

    if save_to_disk and path_obj is not None:
        try:
            save_project_atomically(
                built,
                path_obj,
                baseline_mtime_ns=baseline_mtime_ns,
                check_conflict=True,
            )
        except SaveConflictError:
            return FmEditCommitResult(
                ok=False,
                errors=("Bestand is extern gewijzigd sinds laden.",),
                affected_fm_ids=(),
                project=None,
                run_result=None,
            )

    if path_obj is None:
        return FmEditCommitResult(
            ok=True,
            errors=(),
            affected_fm_ids=(),
            project=built,
            run_result=None,
        )

    try:
        incremental = run_incremental_analysis(
            built,
            path_obj,
            full_recompute=False,
        )
    except Exception as exc:
        log_adapter_exception(
            "rcm_desktop.adapter.fm_edit_commit_service",
            exc,
            context="incrementele analyse na fm-edit commit mislukt",
        )
        return FmEditCommitResult(
            ok=False,
            errors=("Incrementele analyse mislukt.",),
            affected_fm_ids=(),
            project=None,
            run_result=None,
        )

    fm_results = list(incremental.fm_results.values())
    run_result = build_run_result(
        built,
        fm_results,
        pbs_results=incremental.pbs_results,
        summary_prefix="Faalwijze opgeslagen",
    )
    return FmEditCommitResult(
        ok=True,
        errors=(),
        affected_fm_ids=tuple(incremental.affected_fm_ids),
        project=built,
        run_result=run_result,
    )
