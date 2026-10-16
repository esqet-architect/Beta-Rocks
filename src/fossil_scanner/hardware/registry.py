"""
Device registry.

Holds all known hardware adapters. Preflight iterates the registry.
Adapters that are not implemented in the current environment register
themselves as unavailable with a clear reason rather than crashing.
"""
from typing import Dict, List, Optional

from .base import HardwareDevice, DeviceStatus


class DeviceRegistry:
    def __init__(self):
        self._devices: Dict[str, HardwareDevice] = {}

    def register(self, device: HardwareDevice) -> None:
        self._devices[device.name] = device

    def unregister(self, name: str) -> None:
        self._devices.pop(name, None)

    def get(self, name: str) -> Optional[HardwareDevice]:
        return self._devices.get(name)

    def all(self) -> List[HardwareDevice]:
        return list(self._devices.values())

    def probe_all(self) -> List[DeviceStatus]:
        return [d.probe() for d in self._devices.values()]


# Module-level default registry populated by hardware/__init__.py
default_registry = DeviceRegistry()
