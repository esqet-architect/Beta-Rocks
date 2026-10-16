"""
Specimen-centric data model.

Design principles:
- Specimen ID is the immutable root node for all field data.
- Physical observations are recorded verbatim (never interpreted at capture time).
- GPS accuracy is retained explicitly, never silently discarded.
- Location visibility policy is stored with the record, not applied at read time.
- Schema version is retained on load; unsupported versions raise.
"""
import json
import os
import datetime
from typing import Dict, Any, Optional, List


SPECIMEN_ID_PREFIX = "FS"
SUPPORTED_SCHEMA_VERSIONS = ("0.1.0", "0.2.0")
CURRENT_SCHEMA_VERSION = "0.2.0"


def generate_specimen_id(prefix: str = SPECIMEN_ID_PREFIX, index: int = 1) -> str:
    """Generate an immutable specimen identifier of the form FS-YYYY-XXXX."""
    year = datetime.datetime.now(datetime.timezone.utc).year
    return f"{prefix}-{year}-{index:04d}"


def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def atomic_write_json(filepath: str, payload: Dict[str, Any]) -> str:
    """
    Write JSON atomically (write-to-temp + rename) so a dying device
    cannot leave a half-written record behind.
    """
    os.makedirs(os.path.dirname(os.path.abspath(filepath)) or ".", exist_ok=True)
    tmp = f"{filepath}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, filepath)
    return filepath


def append_jsonl(filepath: str, record: Dict[str, Any]) -> str:
    """Append a single record to a JSONL file (durable per-observation storage)."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)) or ".", exist_ok=True)
    with open(filepath, "a") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return filepath


class SpecimenRecord:
    VISIBILITY_CHOICES = ("exact", "generalized", "withheld")

    def __init__(
        self,
        specimen_id: str,
        label: str = "",
        location_visibility: str = "exact",
        notes: str = "",
        created_at: Optional[str] = None,
        schema_version: Optional[str] = None,
    ):
        if location_visibility not in self.VISIBILITY_CHOICES:
            raise ValueError(
                f"location_visibility must be one of {self.VISIBILITY_CHOICES}"
            )
        self.specimen_id = specimen_id
        self.label = label
        self.location_visibility = location_visibility
        self.notes = notes
        self.created_at = created_at or _utcnow_iso()
        self.schema_version = schema_version or CURRENT_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "specimen_id": self.specimen_id,
            "label": self.label,
            "location_visibility": self.location_visibility,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    def save(self, target_dir: str) -> str:
        os.makedirs(target_dir, exist_ok=True)
        return atomic_write_json(
            os.path.join(target_dir, "specimen.json"), self.to_dict()
        )

    @classmethod
    def load(cls, specimen_dir: str) -> "SpecimenRecord":
        with open(os.path.join(specimen_dir, "specimen.json")) as f:
            data = json.load(f)
        stored_version = data.get("schema_version", "0.1.0")
        if stored_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                f"Unsupported schema_version '{stored_version}'. "
                f"Supported: {SUPPORTED_SCHEMA_VERSIONS}"
            )
        return cls(
            specimen_id=data["specimen_id"],
            label=data.get("label", ""),
            location_visibility=data.get("location_visibility", "exact"),
            notes=data.get("notes", ""),
            created_at=data.get("created_at"),
            schema_version=stored_version,
        )
