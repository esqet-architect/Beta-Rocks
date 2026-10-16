# Hardware Integration

## Turntable

Two backends ship in this package.

### ManualTurntableBackend

No hardware. The operator advances the stage by hand. `current_angle()`
returns the last requested angle. Suitable for low-volume manual work.

### SerialTurntableBackend

Generic line protocol. Your firmware should accept:

