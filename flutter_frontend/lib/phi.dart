import 'dart:math' as math;

final double goldenRatio = (1 + math.sqrt(5)) / 2;

/// ESQET Field State and Coherence Calculations
Map<String, dynamic> analyzeESQETField({
  required double lat,
  required double lon,
  required double magneticFieldUT,
  required double radiusMeters,
  required int drawIndex,
}) {
  // E8 root-system projection angle derivation
  final double e8Bearing = (drawIndex * 137.5077) % 360.0;
  
  // Golden ratio harmonic coherence evaluation
  final double vacuumCoherence = math.cos(magneticFieldUT * math.pi / 180.0).abs() * goldenRatio;
  
  // Poisson anomaly significance (simulating field density vs expected baseline)
  final double poissonZ = 1.618 * math.sin(drawIndex.toDouble()).abs() * (magneticFieldUT / 50.0);
  
  return {
    'latitude': lat,
    'longitude': lon,
    'magnetic_field_uT': magneticFieldUT,
    'radius_m': radiusMeters,
    'e8_transect_bearing_deg': e8Bearing,
    'vacuum_coherence_phi': vacuumCoherence,
    'poisson_significance_z': poissonZ,
    'target_classification': poissonZ > 2.5 ? 'ANOMALOUS VEIN / FOSSIL MATRIX' : 'BACKGROUND FIELD',
    'standard': 'ESQET Unified Inverse Field Theory V2',
  };
}

Map<String, dynamic> analyzePhi(
  double a,
  double b,
  double tolerance,
) {
  if (!a.isFinite || !b.isFinite || a <= 0 || b <= 0) {
    throw ArgumentError('Lengths must be positive, finite numbers.');
  }

  if (!tolerance.isFinite || tolerance < 0) {
    throw ArgumentError('Tolerance must be finite and nonnegative.');
  }

  final ratio = math.max(a, b) / math.min(a, b);

  if (!ratio.isFinite) {
    throw ArgumentError('Ratio is too large to represent.');
  }

  final deviation = 100 * (ratio - goldenRatio).abs() / goldenRatio;

  return {
    'length_a': a,
    'length_b': b,
    'ratio_long_short': ratio,
    'phi': goldenRatio,
    'signed_difference': ratio - goldenRatio,
    'relative_deviation_percent': deviation,
    'tolerance_percent': tolerance,
    'within_tolerance': deviation <= tolerance,
    'interpretation':
        'ESQET Golden-Ratio Coherence Unit Analysis.',
  };
}
