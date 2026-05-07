from __future__ import annotations

from typing import Any


class _FallbackSession:
    def __init__(self) -> None:
        self.session_state: dict[str, Any] = {}


def get_session_state() -> dict[str, Any]:
    try:
        import streamlit as st

        return st.session_state
    except ModuleNotFoundError:
        if not hasattr(get_session_state, "_fallback"):
            setattr(get_session_state, "_fallback", _FallbackSession())
        fallback = getattr(get_session_state, "_fallback")
        return fallback.session_state

