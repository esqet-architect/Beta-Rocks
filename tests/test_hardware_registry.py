from fossil_scanner.hardware.registry import DeviceRegistry
from fossil_scanner.hardware.base import HardwareDevice, DeviceStatus


class _FakeDevice(HardwareDevice):
    @property
    def name(self):
        return "fake"

    @property
    def kind(self):
        return "test"

    def probe(self):
        return DeviceStatus(
            name=self.name, kind=self.kind, available=True,
            tested=False, reason="probe only",
        )

    def initialize(self):
        return True


def test_register_and_get():
    reg = DeviceRegistry()
    dev = _FakeDevice()
    reg.register(dev)
    assert reg.get("fake") is dev


def test_probe_all_returns_status():
    reg = DeviceRegistry()
    reg.register(_FakeDevice())
    statuses = reg.probe_all()
    assert len(statuses) == 1
    assert statuses[0].name == "fake"
