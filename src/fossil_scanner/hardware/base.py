"""
Hardware abstraction base.

Every peripheral adapter inherits from HardwareDevice and reports a
consistent status structure so the preflight system can aggregate
availability across all devices without knowing their specifics.
"""
import abc
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class DeviceStatus:
    name: str
    kind: str
    available: bool
    tested: bool
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "available": self.available,
            "tested": self.tested,
            "reason": self.reason,
            "details": self.details,
        }


class HardwareDevice(abc.ABC):
    """
    Abstract base for any peripheral.

    Subclasses must implement:
      - name (property)
      - kind (property)
      - probe() -> DeviceStatus
      - initialize() -> bool
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def kind(self) -> str:
        ...

    @abc.abstractmethod
    def probe(self) -> DeviceStatus:
        """Check whether the device is present and reachable."""
        ...

    @abc.abstractmethod
    def initialize(self) -> bool:
        """Bring the device to a ready state. Return True on success."""
        ...

    def shutdown(self) -> None:
        """Optional cleanup. Default is a no-op."""
        return None
