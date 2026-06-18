"""Qt-vrije FM-detail weergave-beslissing (slice 75)."""



from __future__ import annotations



from dataclasses import dataclass

from enum import Enum





class ColumnFitMode(str, Enum):

    """Weergavemodus voor FM-detail celtekst (viewport-autofit is altijd actief)."""



    PASSEND = "passend"  # regelomloop aan (standaard)

    BIJGESNEDEN = "bijgesneden"  # regelomloop uit (enkele regel)





# FM-detail kolomindices in FMResultsTableModel.

FM_DETAIL_COL_BOUWDEEL = 1

FM_DETAIL_COL_FAALWIJZE = 2



FM_DETAIL_STRETCH_COLUMNS: frozenset[int] = frozenset(

    {FM_DETAIL_COL_FAALWIJZE, FM_DETAIL_COL_BOUWDEEL}

)





def default_column_fit_mode() -> ColumnFitMode:

    return ColumnFitMode.PASSEND





def is_stretch_column(column_index: int) -> bool:

    return column_index in FM_DETAIL_STRETCH_COLUMNS





@dataclass(frozen=True)

class ColumnFitDecision:

    word_wrap: bool

    elide_enabled: bool





def decide_column_fit(mode: ColumnFitMode) -> ColumnFitDecision:

    if mode is ColumnFitMode.PASSEND:

        return ColumnFitDecision(word_wrap=True, elide_enabled=False)

    return ColumnFitDecision(word_wrap=False, elide_enabled=True)


