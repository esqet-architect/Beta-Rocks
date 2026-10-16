import 'dart:math' as math;

final double goldenRatio = (1 + math.sqrt(5)) / 2;

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
        'Numerical proximity only; not fossil identification '
        'or evidence of a golden spiral.',
  };
}
