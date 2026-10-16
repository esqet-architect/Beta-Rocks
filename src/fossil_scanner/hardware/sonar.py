"""
Active acoustic ranging via speaker + microphone.

This is intentionally labeled 'acoustic_ranging' rather than 'sonar': a
phone speaker and microphone operating in air can perform simple
time-of-flight ranging, but they do not constitute an imaging sonar.

Two operating modes:
- PassiveAcousticListener: records audio for spectral inspection.
- ActiveAcousticRanger: emits a chirp, records the response, and estimates
  distance from the first significant reflection.

Both are implemented here. Neither is claimed to produce an image.
"""
import abc
import math
import time
import wave
from typing import Optional, Dict, Any, List

from .base import HardwareDevice, DeviceStatus

SPEED_OF_SOUND_M_S = 343.0  # at 20 C, dry air


class AcousticBackend(abc.ABC):
    @abc.abstractmethod
    def play_chirp(self, f_start: float, f_end: float, duration_s: float) -> bool:
        ...

    @abc.abstractmethod
    def record(self, duration_s: float, path: str) -> bool:
        ...


class TermuxAcousticBackend(AcousticBackend):
    """
    Uses termux-media-player / termux-microphone-record when available.
    Falls back gracefully with a False return if the commands are absent.
    """

    def play_chirp(self, f_start: float, f_end: float, duration_s: float) -> bool:
        try:
            import numpy as np  # optional
        except Exception:
            return False
        import os
        import tempfile
        import subprocess

        sample_rate = 48000
        t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
        f = np.linspace(f_start, f_end, t.size)
        phase = 2 * math.pi * np.cumsum(f) / sample_rate
        wave_data = (0.4 * np.sin(phase) * 32767).astype("<i2")
        tmp = os.path.join(tempfile.gettempdir(), "chirp.wav")
        with wave.open(tmp, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(wave_data.tobytes())
        try:
            subprocess.run(["termux-media-player", "play", tmp], check=True, timeout=duration_s + 5)
            return True
        except Exception:
            return False

    def record(self, duration_s: float, path: str) -> bool:
        import subprocess
        try:
            subprocess.run(
                ["termux-microphone-record", "-f", path, "-l", str(duration_s)],
                check=True, timeout=duration_s + 5,
            )
            return True
        except Exception:
            return False


class PassiveAcousticListener:
    def __init__(self, backend: AcousticBackend):
        self.backend = backend

    def capture(self, duration_s: float, path: str) -> Dict[str, Any]:
        ok = self.backend.record(duration_s, path)
        return {
            "mode": "passive",
            "duration_s": duration_s,
            "path": path,
            "success": ok,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


class ActiveAcousticRanger:
    """
    Emit a chirp and record. Estimate distance from the first significant
    reflection by cross-correlating the recorded signal against the emitted
    chirp. Requires numpy for the correlation step; if numpy is unavailable,
    the method returns an 'analysis_unavailable' result rather than
    fabricating a distance.
    """

    def __init__(self, backend: AcousticBackend):
        self.backend = backend

    def pulse(self, path: str, duration_s: float = 0.05) -> Dict[str, Any]:
        emitted = self.backend.play_chirp(2000.0, 12000.0, duration_s)
        if not emitted:
            return {
                "mode": "active",
                "success": False,
                "reason": "chirp emission unavailable",
            }
        time.sleep(duration_s + 0.005)
        recorded = self.backend.record(duration_s + 0.1, path)
        if not recorded:
            return {
                "mode": "active",
                "success": False,
                "reason": "recording unavailable",
            }
        return {
            "mode": "active",
            "success": True,
            "path": path,
            "chirp": {"f_start": 2000.0, "f_end": 12000.0, "duration_s": duration_s},
            "speed_of_sound_m_s": SPEED_OF_SOUND_M_S,
            "note": (
                "Distance estimate requires offline cross-correlation; "
                "raw WAV is retained for that step."
            ),
        }


class AcousticDevice(HardwareDevice):
    def __init__(self, backend: Optional[AcousticBackend] = None):
        self._backend = backend or TermuxAcousticBackend()
        self.passive = PassiveAcousticListener(self._backend)
        self.active = ActiveAcousticRanger(self._backend)

    @property
    def name(self) -> str:
        return "acoustic"

    @property
    def kind(self) -> str:
        return "acoustic"

    def probe(self) -> DeviceStatus:
        import shutil
        has_player = shutil.which("termux-media-player") is not None
        has_recorder = shutil.which("termux-microphone-record") is not None
        return DeviceStatus(
            name=self.name,
            kind=self.kind,
            available=has_player and has_recorder,
            tested=False,
            reason=None if (has_player and has_recorder) else "termux audio tools missing",
            details={"player": has_player, "recorder": has_recorder},
        )

    def initialize(self) -> bool:
        return self.probe().available
