"""Slice 75 issue 01 — FM-detail viewport-plan + display-beslissing (Qt-vrij)."""



from __future__ import annotations



from rcm_desktop.adapter.column_fit_policy import (

    FM_DETAIL_COL_BOUWDEEL,

    FM_DETAIL_COL_FAALWIJZE,

    ColumnFitMode,

    decide_column_fit,

    default_column_fit_mode,

    is_stretch_column,

)





def test_default_column_fit_mode_is_passend() -> None:

    assert default_column_fit_mode() is ColumnFitMode.PASSEND





def test_viewport_plan_stretch_on_text_columns_only() -> None:

    assert is_stretch_column(FM_DETAIL_COL_FAALWIJZE) is True

    assert is_stretch_column(FM_DETAIL_COL_BOUWDEEL) is True

    assert is_stretch_column(0) is False

    assert is_stretch_column(3) is False

    assert is_stretch_column(4) is False





def test_passend_enables_word_wrap_without_elide() -> None:

    decision = decide_column_fit(ColumnFitMode.PASSEND)

    assert decision.word_wrap is True

    assert decision.elide_enabled is False





def test_bijgesneden_disables_word_wrap_and_enables_elide() -> None:

    decision = decide_column_fit(ColumnFitMode.BIJGESNEDEN)

    assert decision.word_wrap is False

    assert decision.elide_enabled is True


