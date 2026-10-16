"""
Turntable control.

Two backends:
- ManualTurntableBackend: operator advances the stage by hand; the app
  prompts at each step. Encoder is simulated by operator input.
- SerialTurntableBackend: G-code-like serial control for a stepper driver.
  The exact protocol is defined by the driver; we implement a generic
  line-based interface and mark it as requiring hardware-specific
  configuration.

Both backends implement the same interface so imaging.py does not need to
know which is in use.
"""
import abc
import time
from typing import Optional, Dict, Any

from .base import HardwareDevice, DeviceStatus


class TurntableBackend(abc.ABC):
    @abc.abstractmethod
    def home(self) -> bool:
        ...

    @abc.abstractmethod
    def rotate_to(self, angle_deg: float) -> bool:
        ...

    @abc.abstractmethod
    def current_angle(self) -> Optional[float]:
        ...

    @abc.abstractmethod
    def step_count(self) -> int:
        ...


class ManualTurntableBackend(TurntableBackend):
    """
    No hardware. The operator is prompted to move the stage.
    current_angle() returns None because no encoder exists.
    """

    def __init__(self):
        self._angle: Optional[float] = None
        self._steps = 0

    def home(self) -> bool:
        self._angle = 0.0
        return True

    def rotate_to(self, angle_deg: float) -> bool:
        self._angle = float(angle_deg)
        self._steps += 1
        return True

    def current_angle(self) -> Optional[float]:
        return self._angle

    def step_count(self) -> int:
        return self._steps


class SerialTurntableBackend(TurntableBackend):
    """
    Generic serial line protocol.

    Real drivers vary; this class intentionally exposes send_line() so a
    firmware-specific subclass can override the command strings.

    Expected firmware behavior (documented in HARDWARE_INTEGRATION.md):
      - accepts lines of the form '<CMD>\\n'
      - responds with 'OK\\n' on success
      - HOME, MOVE <deg>, GETPOS
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None
        self._steps = 0

    def _ensure_open(self) -> bool:
        if self._serial is not None:
            return True
        try:
            import serial  # pyserial
            self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(0.2)
            return True
        except Exception:
            return False

    def send_line(self, cmd: str) -> Optional[str]:
        if not self._ensure_open():
            return None
        try:
            self._serial.write((cmd + "\n").encode("ascii"))
            self._serial.flush()
            return self._serial.readline().decode("ascii", errors="replace").strip()
        except Exception:
            return None

    def home(self) -> bool:
        resp = self.send_line("HOME")
        return resp == "OK"

    def rotate_to(self, angle_deg: float) -> bool:
        resp = self.send_line(f"MOVE {angle_deg:.3f}")
        if resp == "OK":
            self._steps += 1
            return True
        return False

    def current_angle(self) -> Optional[float]:
        resp = self.send_line("GETPOS")
        if resp is None:
            return None
        try:
            return float(resp)
        except ValueError:
            return None

    def step_count(self) -> int:
        return self._steps


class TurntableDevice(HardwareDevice):
    def __init__(self, backend: Optional[TurntableBackend] = None):
        self._backend = backend or ManualTurntableBackend()

    @property
    def name(self) -> str:
        return "turntable"

    @property
    def kind(self) -> str:
        return "motion"

    def probe(self) -> DeviceStatus:
        is_serial = isinstance(self._backend, SerialTurntableBackend)
        return DeviceStatus(
            name=self.name,
            kind=self.kind,
            available=True,
            tested=False,
            reason=None if is_serial else "manual backend (no encoder)",
            details={"backend": type(self._backend).__name__},
        )

    def initialize(self) -> bool:
        return self._backend.home()

    @property
    def backend(self) -> TurntableBackend:
        return self._backend
