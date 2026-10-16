"""
Append-only acquisition log.

Every mutating operation emits one event. This is the audit trail that
allows a report to be reconstructed from primary evidence.
"""
import json
import os
import datetime
import uuid
from typing import Dict, Any, Optional

EVENT_TYPES = (
    "SPECIMEN_CREATED",
    "GPS_FIX",
    "BASELINE_CAPTURED",
    "MAGNETIC_SAMPLE",
    "SURVEY_STARTED",
    "SURVEY_COMPLETED",
    "IMAGE_CAPTURED",
    "IMAGE_HASHED",
    "CALIBRATION_CREATED",
    "ANALYSIS_STARTED",
    "CLASSIFICATION_UPDATED",
    "REPORT_GENERATED",
    "INTEGRITY_VERIFIED",
    "HARDWARE_PREFLIGHT",
    "TURNTABLE_STEP",
    "SONAR_PULSE",
    "METAL_DETECTOR_READING",
    "LIDAR_IMPORTED",
    "THERMAL_FRAME",
    "IDENTIFICATION_RUN",
    "REFERENCE_PACK_INSTALLED",
    "PHI_ANALYSIS",
    "TORSION_MEASURED",
    "BRUSHING_SESSION",
)


def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class ProvenanceLog:
    """One log per specimen. Events append-only, JSONL format."""

    def __init__(self, specimen_dir: str):
        self.specimen_dir = specimen_dir
        self.path = os.path.join(specimen_dir, "acquisition.jsonl")
        os.makedirs(specimen_dir, exist_ok=True)

    def record(
        self,
        event: str,
        specimen_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if event not in EVENT_TYPES:
            raise ValueError(f"Unknown event type: {event}")
        entry = {
            "event_id": str(uuid.uuid4()),
            "timestamp_utc": _utcnow_iso(),
            "event": event,
            "specimen_id": specimen_id,
            "payload": payload or {},
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return entry

    def read_all(self) -> list:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return [json.loads(line) for line in f if line.strip()]

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify the log is parseable and that event_ids are unique.
        This detects tampering/duplication but not a coordinated rewrite.
        """
        events = self.read_all()
        ids = [e.get("event_id") for e in events]
        unique = len(set(ids)) == len(ids)
        return {
            "event_count": len(events),
            "unique_event_ids": unique,
            "status": "ok" if unique else "duplicate_event_ids_detected",
        }
