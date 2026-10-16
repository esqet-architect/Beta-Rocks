"""
Metal detector integration.

Three data sources, kept explicitly separate:
1. The phone's magnetometer (already in sensors.py) - magnetic response.
2. A CSV import from a consumer metal detector's logged output.
3. A serial adapter for detectors that expose a data stream.

There is no universal metal-detector protocol. The serial adapter is
therefore a thin line reader that the operator configures.
"""
import abc
import csv
import os
from typing import Optional, Dict, Any, List

from .base import HardwareDevice, DeviceStatus


class MetalDetectorBackend(abc.ABC):
    @abc.abstractmethod
    def read_reading(self) -> Optional[Dict[str, Any]]:
        ...


class CSVImportBackend(MetalDetectorBackend):
    """
    Reads a previously exported CSV. Expected columns (case-insensitive):
    timestamp, signal, target_id (optional), depth_cm (optional)
    Extra columns are preserved in 'raw'.
    """

    def __init__(self, path: str):
        self.path = path
        self._rows: List[Dict[str, Any]] = []
        self._idx = 0
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self._rows.append({k.lower(): v for k, v in row.items()})

    def read_reading(self) -> Optional[Dict[str, Any]]:
        if self._idx >= len(self._rows):
            return None
        row = self._rows[self._idx]
        self._idx += 1
        return {
            "timestamp": row.get("timestamp"),
            "signal": row.get("signal"),
            "target_id": row.get("target_id"),
            "depth_cm": row.get("depth_cm"),
            "raw": row,
        }

    def __len__(self) -> int:
        return len(self._rows)


class SerialMetalDetectorBackend(MetalDetectorBackend):
    """
    Generic serial line reader. Firmware-specific parsing belongs in a
    subclass. Base class assumes one reading per line, JSON-encoded.
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

    def _ensure_open(self) -> bool:
        if self._serial is not None:
            return True
        try:
            import serial
            self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            return True
        except Exception:
            return False

    def read_reading(self) -> Optional[Dict[str, Any]]:
        if not self._ensure_open():
            return None
        try:
            line = self._serial.readline().decode("ascii", errors="replace").strip()
            if not line:
                return None
            import json
            return json.loads(line)
        except Exception:
            return None


class MetalDetectorDevice(HardwareDevice):
    def __init__(self, backend: Optional[MetalDetectorBackend] = None):
        self._backend = backend

    @property
    def name(self) -> str:
        return "metal_detector"

    @property
    def kind(self) -> str:
        return "detector"

    def probe(self) -> DeviceStatus:
        if self._backend is None:
            return DeviceStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                tested=False,
                reason="no backend configured (CSV import or serial required)",
            )
        if isinstance(self._backend, CSVImportBackend):
            return DeviceStatus(
                name=self.name,
                kind=self.kind,
                available=len(self._backend) > 0,
                tested=False,
                reason=None if len(self._backend) > 0 else "CSV contains no rows",
                details={"rows": len(self._backend)},
            )
        return DeviceStatus(
            name=self.name,
            kind=self.kind,
            available=True,
            tested=False,
            details={"backend": type(self._backend).__name__},
        )

    def initialize(self) -> bool:
        return self.probe().available

    @property
    def backend(self) -> Optional[MetalDetectorBackend]:
        return self._backend
