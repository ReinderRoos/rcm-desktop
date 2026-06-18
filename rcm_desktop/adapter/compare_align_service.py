"""FM-uitlijning voor dual-project compare (slice 95 issue 05, slice 96 issue 02)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from rcm_core.library_distill import fm_technical_fingerprint
from rcm_core.models import RCMProject


@dataclass(frozen=True)
class FailureModePair:
    fm_id_a: str | None
    fm_id_b: str | None
    match_kind: str  # id | fingerprint | manual | unmatched_a | unmatched_b


def _fingerprint(project: RCMProject, fm_id: str) -> str:
    return fm_technical_fingerprint(project.faalwijzes[fm_id], project.config)


def align_failure_modes(project_a: RCMProject, project_b: RCMProject) -> tuple[FailureModePair, ...]:
    ids_a = set(project_a.faalwijzes.keys())
    ids_b = set(project_b.faalwijzes.keys())
    matched_ids = sorted(ids_a & ids_b)
    only_a = sorted(ids_a - ids_b)
    only_b = sorted(ids_b - ids_a)

    pairs: list[FailureModePair] = [
        FailureModePair(fm_id_a=fm_id, fm_id_b=fm_id, match_kind="id") for fm_id in matched_ids
    ]

    b_by_fingerprint: dict[str, list[str]] = defaultdict(list)
    for fm_id_b in only_b:
        b_by_fingerprint[_fingerprint(project_b, fm_id_b)].append(fm_id_b)
    for fp in b_by_fingerprint:
        b_by_fingerprint[fp].sort()

    matched_fp_a: set[str] = set()
    matched_fp_b: set[str] = set()
    for fm_id_a in only_a:
        fp = _fingerprint(project_a, fm_id_a)
        candidates = [fm_id for fm_id in b_by_fingerprint.get(fp, []) if fm_id not in matched_fp_b]
        if not candidates:
            continue
        fm_id_b = candidates[0]
        pairs.append(
            FailureModePair(fm_id_a=fm_id_a, fm_id_b=fm_id_b, match_kind="fingerprint")
        )
        matched_fp_a.add(fm_id_a)
        matched_fp_b.add(fm_id_b)

    pairs.extend(
        FailureModePair(fm_id_a=fm_id, fm_id_b=None, match_kind="unmatched_a")
        for fm_id in only_a
        if fm_id not in matched_fp_a
    )
    pairs.extend(
        FailureModePair(fm_id_a=None, fm_id_b=fm_id, match_kind="unmatched_b")
        for fm_id in only_b
        if fm_id not in matched_fp_b
    )
    return tuple(pairs)
