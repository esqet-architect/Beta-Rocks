"""
Imaging and turntable capture.

Integrates with the turntable hardware abstraction so that manual and
motorized capture use the same code path. Each capture is timestamped,
hashed, and linked to a specimen and a turntable step (when available).
"""
import datetime
import os
import uuid
from typing import Dict, Any, Optional, List

from .schema import append_jsonl
from .provenance import ProvenanceLog
from .hashing import hash_file
from .hardware.turntable import TurntableBackend


def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def capture_image(
    image_path: str,
    specimen_id: str,
    specimen_dir: str,
    view_label: str = "lateral",
    turntable_angle_deg: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Register an existing image file (taken by the device camera or
    imported) into the specimen's image log.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(image_path)
    sha = hash_file(image_path)
    entry = {
        "image_id": str(uuid.uuid4()),
        "timestamp_utc": _utcnow_iso(),
        "specimen_id": specimen_id,
        "path": image_path,
        "sha256": sha,
        "view_label": view_label,
        "turntable_angle_deg": turntable_angle_deg,
    }
    append_jsonl(os.path.join(specimen_dir, "images.jsonl"), entry)
    ProvenanceLog(specimen_dir).record(
        "IMAGE_CAPTURED",
        specimen_id=specimen_id,
        payload={"image_id": entry["image_id"], "sha256": sha, "view": view_label},
    )
    return entry


def run_turntable_capture(
    specimen_id: str,
    specimen_dir: str,
    turntable: TurntableBackend,
    capture_callback,
    steps: int = 36,
    rings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Iterate a full revolution at each requested ring, calling
    capture_callback(angle_deg, ring_label) at each step. capture_callback
    is supplied by the app because the actual camera invocation is
    platform-specific.
    """
    rings = rings or ["low", "middle", "high"]
    step_deg = 360.0 / steps
    captured = []
    log = ProvenanceLog(specimen_dir)
    log.record(
        "SURVEY_STARTED",
        specimen_id=specimen_id,
        payload={"mode": "turntable", "steps": steps, "rings": rings},
    )

    if not turntable.home():
        return {"success": False, "reason": "turntable home failed"}

    for ring in rings:
        for i in range(steps):
            angle = i * step_deg
            turntable.rotate_to(angle)
            actual = turntable.current_angle()
            result = capture_callback(angle, ring)
            entry = {
                "ring": ring,
                "step": i,
                "requested_angle_deg": angle,
                "reported_angle_deg": actual,
                "capture": result,
            }
            captured.append(entry)
            log.record("TURNTABLE_STEP", specimen_id=specimen_id, payload=entry)

    summary = {
        "success": True,
        "specimen_id": specimen_id,
        "rings": rings,
        "steps_per_ring": steps,
        "total_captures": len(captured),
    }
    log.record("SURVEY_COMPLETED", specimen_id=specimen_id, payload=summary)
    return summary
