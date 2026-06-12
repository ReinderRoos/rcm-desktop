"""Gedeelde commit-façade voor faalwijze-editor en grid (slice 50)."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.fm_edit_bundle_service import FmEditBundle
from rcm_desktop.adapter.fm_edit_commit_service import (
    FmEditCommitResult,
    apply_fm_scope,
    commit_edits,
    replace_fm_scope,
)


class RunPolicy(Enum):
    """Hoe incrementele run wordt uitgevoerd (async via RunRunner blijft in de view)."""

    BLOCKING = "blocking"


def commit_fm_edit(
    session: EditingSession,
    bundle: FmEditBundle | None,
    *,
    path: Path | str | None = None,
    save_to_disk: bool = False,
    baseline_mtime_ns: int | None = None,
    run_policy: RunPolicy = RunPolicy.BLOCKING,
) -> FmEditCommitResult:
    """Valideer, materialiseer en optioneel save + incrementele run voor FM-edit."""
    del run_policy  # async pad blijft FmEditCommitRunner; façade deelt validate→run-logica
    if bundle is not None:
        apply_fm_scope(session, bundle)
    return commit_edits(
        session,
        project_path=path,
        save_to_disk=save_to_disk,
        baseline_mtime_ns=baseline_mtime_ns,
    )
