import json
import os
import tempfile
import pytest
from fossil_scanner.schema import SpecimenRecord


def test_round_trip_preserves_created_at():
    with tempfile.TemporaryDirectory() as d:
        rec = SpecimenRecord("FS-2026-0001", label="test")
        rec.save(d)
        loaded = SpecimenRecord.load(d)
        assert loaded.created_at == rec.created_at
        assert loaded.schema_version == rec.schema_version


def test_unsupported_version_raises():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "specimen.json"), "w") as f:
            json.dump({"schema_version": "99.0.0", "specimen_id": "FS-2026-0001"}, f)
        with pytest.raises(ValueError):
            SpecimenRecord.load(d)
