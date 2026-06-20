"""Frame gallery calculation helpers used by the Streamlit UI."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def resolve_phase_threshold(
    frame_data: Mapping,
    threshold: float | None,
    *,
    segment_bounds: Sequence[int] | None,
    phase_error: Mapping[str, float],
) -> float:
    if threshold is not None:
        return threshold
    if segment_bounds:
        idx = int(frame_data.get("index", 1) or 1) - 1
        n0, n1, n2, n3 = segment_bounds
        if n0 <= idx < n1:
            return phase_error["g1"]
        if n1 <= idx < n2:
            return phase_error["g2"]
        if n2 <= idx < n3:
            return phase_error["g3"]
    return phase_error["g2"]


def frame_phase_status(
    frame_data: Mapping,
    threshold: float | None,
    *,
    is_gay_exercise: bool,
    segment_bounds: Sequence[int] | None,
    phase_error: Mapping[str, float],
    near_multiplier: float = 1.5,
) -> str:
    threshold = resolve_phase_threshold(
        frame_data,
        threshold,
        segment_bounds=segment_bounds,
        phase_error=phase_error,
    )
    eval_info = frame_data.get("eval_info", {}) or {}
    shoulder_ref = eval_info.get("shoulder_ref", 90)
    elbow_ref = eval_info.get("elbow_ref", 170)

    if is_gay_exercise:
        shoulder_left = frame_data.get("goc_vai_trai")
        shoulder_right = frame_data.get("goc_vai_phai")
        elbow_left = frame_data.get("goc_khuyu_trai")
        elbow_right = frame_data.get("goc_khuyu_phai")
        if shoulder_left is None or shoulder_right is None or elbow_left is None or elbow_right is None:
            return "FAIL"
        shoulder_pass = abs(shoulder_left - shoulder_ref) <= threshold and abs(shoulder_right - shoulder_ref) <= threshold
        elbow_pass = abs(elbow_left - elbow_ref) <= threshold and abs(elbow_right - elbow_ref) <= threshold
        shoulder_near = (
            abs(shoulder_left - shoulder_ref) <= threshold * near_multiplier
            and abs(shoulder_right - shoulder_ref) <= threshold * near_multiplier
        )
        elbow_near = (
            abs(elbow_left - elbow_ref) <= threshold * near_multiplier
            and abs(elbow_right - elbow_ref) <= threshold * near_multiplier
        )
    else:
        shoulder_angle = frame_data.get("goc_vai")
        elbow_angle = frame_data.get("goc_khuyu")
        if shoulder_angle is None or elbow_angle is None:
            return "FAIL"
        shoulder_pass = abs(shoulder_angle - shoulder_ref) <= threshold
        elbow_pass = abs(elbow_angle - elbow_ref) <= threshold
        shoulder_near = abs(shoulder_angle - shoulder_ref) <= threshold * near_multiplier
        elbow_near = abs(elbow_angle - elbow_ref) <= threshold * near_multiplier

    if shoulder_pass and elbow_pass:
        return "PASS"
    if shoulder_near and elbow_near:
        return "NEAR"
    return "FAIL"


def filter_frame_indices(
    indices: Sequence[int],
    frame_data_list: Sequence[Mapping],
    sub_filter: str,
    status_fn,
) -> list[int]:
    if sub_filter not in {"PASS", "NEAR", "FAIL"}:
        return list(indices)
    return [idx for idx in indices if status_fn(frame_data_list[idx]) == sub_filter]


def frame_status_counts(indices: Sequence[int], frame_data_list: Sequence[Mapping], status_fn) -> dict[str, int]:
    counts = {"PASS": 0, "NEAR": 0, "FAIL": 0}
    for idx in indices:
        status = status_fn(frame_data_list[idx])
        counts[status] = counts.get(status, 0) + 1
    return counts


def paginate_indices(indices: Sequence[int], *, page: int, per_page: int) -> tuple[list[int], int, int, int]:
    total = len(indices)
    per_page = max(1, int(per_page or 1))
    total_pages = max(1, (total + per_page - 1) // per_page)
    current_page = min(max(1, int(page or 1)), total_pages)
    start = (current_page - 1) * per_page
    end = min(start + per_page, total)
    return list(indices[start:end]), current_page, total_pages, total
