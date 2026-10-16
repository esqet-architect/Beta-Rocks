"""
Survey modes: spot, grid, transect.

All modes emit observations to observations.jsonl (append-only) and a
summary to survey.json. Each observation is independently recoverable if
the device dies mid-survey. Absent measurements are represented as None.
"""
import datetime
import os
import uuid
from typing import Dict, Any, Optional, List

from .magnetometer import process_magnetic_samples, anomaly_classification
from .gps import acquire_gps_point
from .sensors import read_termux_magnetometer
from .schema import append_jsonl, atomic_write_json
from .provenance import ProvenanceLog


def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _next_observation_id(specimen_dir: str) -> str:
    path = os.path.join(specimen_dir, "observations.jsonl")
    n = 0
    if os.path.exists(path):
        with open(path) as f:
            for _ in f:
                n += 1
    return f"MAG-{n + 1:06d}"


def _collect_samples(samples: int) -> Dict[str, Any]:
    res = read_termux_magnetometer(samples=samples)
    if not res.get("available"):
        return {
            "samples": [],
            "status": "unavailable",
            "reason": res.get("reason", "unknown"),
            "raw": None,
        }
    return {
        "samples": res.get("samples", []),
        "status": "ok",
        "reason": None,
        "raw": res.get("raw"),
    }


def _make_observation(
    specimen_id: Optional[str],
    specimen_dir: Optional[str],
    survey_meta: Dict[str, Any],
    samples: int,
    baseline: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    acq = _collect_samples(samples)
    stats = process_magnetic_samples(acq["samples"])

    obs = {
        "observation_id": _next_observation_id(specimen_dir) if specimen_dir else str(uuid.uuid4()),
        "timestamp_utc": _utcnow_iso(),
        "specimen_id": specimen_id,
        "survey": survey_meta,
        "sensor": {"name": "magnetometer", "units": "uT"},
        "field": {
            "x_uT": stats["vector_mean"]["x_uT"],
            "y_uT": stats["vector_mean"]["y_uT"],
            "z_uT": stats["vector_mean"]["z_uT"],
            "magnitude_uT": stats["magnitude"]["median_uT"],
        },
        "statistics": {
            "n": stats["count"],
            "median_uT": stats["magnitude"]["median_uT"],
            "mad_uT": stats["magnitude"]["mad_uT"],
            "robust_sigma_uT": stats["magnitude"]["robust_sigma_uT"],
        },
        "gps": None,
        "acquisition": {"status": acq["status"], "reason": acq["reason"]},
        "quality": {"status": "valid" if acq["samples"] else "no_samples"},
    }

    if baseline and stats["count"]:
        obs["baseline"] = {
            "magnitude_uT": baseline.get("magnitude_uT"),
            "delta_uT": (
                round(stats["magnitude"]["median_uT"] - baseline["magnitude_uT"], 4)
                if baseline.get("magnitude_uT") is not None else None
            ),
        }
    obs["anomaly"] = anomaly_classification(
        magnitude_uT=stats["magnitude"]["median_uT"],
        center_uT=baseline.get("magnitude_uT") if baseline else None,
        scale_uT=baseline.get("scale_uT") if baseline else None,
    )
    return obs


def run_spot_survey(
    specimen_id: Optional[str] = None,
    specimen_dir: Optional[str] = None,
    samples: int = 15,
    gps_visibility: str = "exact",
    baseline: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if specimen_dir:
        ProvenanceLog(specimen_dir).record(
            "SURVEY_STARTED",
            specimen_id=specimen_id,
            payload={"mode": "spot", "samples": samples},
        )
    obs = _make_observation(specimen_id, specimen_dir, {"mode": "spot"}, samples, baseline)
    obs["gps"] = acquire_gps_point(visibility=gps_visibility)
    if specimen_dir:
        append_jsonl(os.path.join(specimen_dir, "observations.jsonl"), obs)
        ProvenanceLog(specimen_dir).record(
            "MAGNETIC_SAMPLE",
            specimen_id=specimen_id,
            payload={
                "observation_id": obs["observation_id"],
                "n": obs["statistics"]["n"],
                "status": obs["acquisition"]["status"],
            },
        )
    return obs


def run_grid_survey(
    specimen_id: Optional[str],
    specimen_dir: str,
    rows: int,
    cols: int,
    spacing_m: float,
    samples_per_point: int = 15,
    gps_visibility: str = "exact",
    baseline: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    log = ProvenanceLog(specimen_dir)
    log.record(
        "SURVEY_STARTED",
        specimen_id=specimen_id,
        payload={"mode": "grid", "rows": rows, "cols": cols, "spacing_m": spacing_m},
    )
    observations = []
    for r in range(rows):
        for c in range(cols):
            obs = _make_observation(
                specimen_id, specimen_dir,
                {"mode": "grid", "row": r, "col": c, "spacing_m": spacing_m},
                samples_per_point, baseline,
            )
            obs["gps"] = acquire_gps_point(visibility=gps_visibility)
            append_jsonl(os.path.join(specimen_dir, "observations.jsonl"), obs)
            observations.append(obs)

    summary = {
        "mode": "grid",
        "rows": rows,
        "cols": cols,
        "count": len(observations),
        "specimen_id": specimen_id,
    }
    atomic_write_json(os.path.join(specimen_dir, "survey.json"), summary)
    log.record("SURVEY_COMPLETED", specimen_id=specimen_id, payload=summary)
    return summary


def run_transect_survey(
    specimen_id: Optional[str],
    specimen_dir: str,
    points: int,
    spacing_m: float,
    samples_per_point: int = 15,
    gps_visibility: str = "exact",
    baseline: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    log = ProvenanceLog(specimen_dir)
    log.record(
        "SURVEY_STARTED",
        specimen_id=specimen_id,
        payload={"mode": "transect", "points": points, "spacing_m": spacing_m},
    )
    observations = []
    for i in range(points):
        obs = _make_observation(
            specimen_id, specimen_dir,
            {"mode": "transect", "index": i, "spacing_m": spacing_m},
            samples_per_point, baseline,
        )
        obs["gps"] = acquire_gps_point(visibility=gps_visibility)
        append_jsonl(os.path.join(specimen_dir, "observations.jsonl"), obs)
        observations.append(obs)

    summary = {
        "mode": "transect",
        "points": points,
        "spacing_m": spacing_m,
        "count": len(observations),
        "specimen_id": specimen_id,
    }
    atomic_write_json(os.path.join(specimen_dir, "survey.json"), summary)
    log.record("SURVEY_COMPLETED", specimen_id=specimen_id, payload=summary)
    return summary
