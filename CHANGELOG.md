# Changelog

## 0.2.0

### Added
- Hardware abstraction layer with turntable, acoustic, metal-detector,
  LiDAR-dataset, and thermal backends.
- Preflight system that probes every registered device and reports
  available / untested / unavailable states.
- Analysis package: phi-ratio measurement, shape descriptors, mineral
  candidate ranking, morphology observation/interpretation split, torsion
  measurement with whole-turn declaration.
- Identification pipeline: candidate retrieval, character matching,
  context ranking, decision policy, structured run records.
- Reference repository (SQLite), pack importer with checksum verification,
  and per-asset attribution.
- COLMAP bridge for external reconstruction.

### Changed
- `SpecimenRecord.load()` now round-trips `created_at` and `schema_version`,
  and rejects unsupported schema versions.
- Missing magnetometer samples are represented as `None`, not zero.
- `anomaly_classification()` returns `indeterminate` with a reason when
  inputs cannot support a classification.
- `make_claim()` enforces that `VERIFIED` requires verification records,
  and that `OBSERVED`/`MEASURED`/`DERIVED`/`MODELED` require a basis.
- Sensor adapter returns a structured acquisition result with samples,
  status, reason, and raw response.

### Notes
- LiDAR is a dataset registry, not a live sensor.
- Acoustic ranging is labeled as such, not as imaging sonar.
- Metal detector integration is CSV or serial; no universal protocol is
  assumed.
- The identification pipeline prefers `unresolved` over a species when
  diagnostic evidence is missing.
