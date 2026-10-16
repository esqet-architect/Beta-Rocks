"""
Thermal capture.

Most phones do not expose a thermal sensor. This module provides a backend
abstraction so that:
- On phones with no sensor, probe() returns available=False.
- With an external FLIR/Seek/MLX90640 over serial or BLE, a backend can be
  plugged in without changing the survey code.
"""
import abc
from typing import Optional, Dict, Any

from .base import HardwareDevice, DeviceStatus


class ThermalBackend(abc.ABC):
    @abc.abstractmethod
    def read_frame(self) -> Optional[Dict[str, Any]]:
        ...


class TermuxThermalBackend(ThermalBackend):
    """
    Attempts to read the device's ambient temperature sensor via
    termux-sensor. This is not a thermal camera; it returns a single scalar.
    Labeled accordingly.
    """

    def read_frame(self) -> Optional[Dict[str, Any]]:
        import subprocess, json
        try:
            res = subprocess.run(
                ["termux-sensor", "-s", "temperature", "-n", "1"],
                capture_output=True, text=True, timeout=5,
            )
            if res.returncode != 0 or not res.stdout.strip():
                return None
            data = json.loads(res.stdout)
            return {"mode": "ambient_scalar", "data": data}
        except Exception:
            return None


class ThermalDevice(HardwareDevice):
    def __init__(self, backend: Optional[ThermalBackend] = None):
        self._backend = backend

    @property
    def name(self) -> str:
        return "thermal"

    @property
    def kind(self) -> str:
        return "thermal"

    def probe(self) -> DeviceStatus:
        if self._backend is None:
            return DeviceStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                tested=False,
                reason="no thermal backend configured",
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
