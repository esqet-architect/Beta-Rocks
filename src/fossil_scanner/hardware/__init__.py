"""
Hardware package.

On import, registers the default device set into the module-level registry.
Callers may register additional backends before running preflight.
"""
from .registry import default_registry
from .turntable import TurntableDevice
from .sonar import AcousticDevice
from .metal_detector import MetalDetectorDevice
from .lidar import LidarDevice
from .thermal import ThermalDevice
from .base import HardwareDevice, DeviceStatus
from .preflight import run_preflight, format_preflight_report


def register_default_devices() -> None:
    default_registry.register(TurntableDevice())
    default_registry.register(AcousticDevice())
    default_registry.register(MetalDetectorDevice())
    default_registry.register(LidarDevice())
    default_registry.register(ThermalDevice())


register_default_devices()

__all__ = [
    "default_registry",
    "HardwareDevice",
    "DeviceStatus",
    "run_preflight",
    "format_preflight_report",
    "register_default_devices",
]
