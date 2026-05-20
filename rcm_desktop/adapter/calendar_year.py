"""Kalenderjaar-mapping voor LTAP/LCC-presentatie.

Horizonindex i (0 = eerste jaar van de lifecycle t.o.v. modeljaar) wordt voor de gebruiker
getoond als kalenderjaar = modeljaar + i (zie RCMConfig.modeljaar).
"""


def calendar_year_for_horizon_index(modeljaar: int, horizon_index: int) -> int:
    return int(modeljaar) + int(horizon_index)
