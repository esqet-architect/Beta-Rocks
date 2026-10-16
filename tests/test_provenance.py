import tempfile
import pytest
from fossil_scanner.provenance import ProvenanceLog


def test_record_and_read():
    with tempfile.TemporaryDirectory() as d:
        log = ProvenanceLog(d)
        log.record("SPECIMEN_CREATED", specimen_id="FS-2026-0001")
        log.record("GPS_FIX", specimen_id="FS-2026-0001")
        events = log.read_all()
        assert len(events) == 2
        assert events[0]["event"] == "SPECIMEN_CREATED"


def test_verify_integrity_reports_ok():
    with tempfile.TemporaryDirectory() as d:
        log = ProvenanceLog(d)
        log.record("SPECIMEN_CREATED", specimen_id="FS-2026-0001")
        result = log.verify_integrity()
        assert result["status"] == "ok"


def test_unknown_event_raises():
    with tempfile.TemporaryDirectory() as d:
        log = ProvenanceLog(d)
        with pytest.raises(ValueError):
            log.record("NOT_A_REAL_EVENT")
