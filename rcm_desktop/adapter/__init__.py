"""Adapterlaag tussen rcm_core en de Qt-views.

Bevat o.a. Qt-models (subklassen van `QAbstractTableModel`/`QAbstractItemModel`)
die de tabulaire editing-pipeline en runresultaten exposen, en een runner-klasse
die `incremental_run.run_incremental_analysis` op een `QThread` draait.
"""
