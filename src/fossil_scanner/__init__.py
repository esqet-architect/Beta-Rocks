"""FossilScanner package."""
from .schema import SpecimenRecord, generate_specimen_id
from .provenance import ProvenanceLog
from .evidence import make_claim, make_classification, transition_claim

__version__ = "0.2.0"

__all__ = [
    "SpecimenRecord",
    "generate_specimen_id",
    "ProvenanceLog",
    "make_claim",
    "make_classification",
    "transition_claim",
]
