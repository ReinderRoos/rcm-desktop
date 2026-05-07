"""Canoniek project in UI-sessie + gelijk trekken met edit-buffers na save/run."""
from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from rcm_core.editing.state import init_edit_state
from rcm_core.models import RCMProject

# Enige sleutel voor het geserialiseerde **domain model** in Streamlit-session_state.
CANONICAL_PROJECT_KEY = "project_data"


def read_canonical_project(session: MutableMapping[str, Any]) -> RCMProject:
    """Lees het canonieke project uit de sessie (lege dict → leeg ``RCMProject``)."""
    raw = session.get(CANONICAL_PROJECT_KEY)
    if raw is None:
        return RCMProject()
    return RCMProject.from_dict(raw)


def write_canonical_project(session: MutableMapping[str, Any], project: RCMProject) -> None:
    """Schrijf het canonieke model als ``to_dict()`` naar de sessie."""
    session[CANONICAL_PROJECT_KEY] = project.to_dict()


def promote_built_to_canonical(session: MutableMapping[str, Any], built: RCMProject) -> None:
    """Na succesvolle save/run: canoniek model en tabulaire buffers gelijkzetten."""
    write_canonical_project(session, built)
    init_edit_state(built, session=session)
