import 'package:flutter_test/flutter_test.dart';
import 'package:fossil_field_console/phi.dart';

void main() {
  test('Exact phi has negligible deviation', () {
    final result = analyzePhi(goldenRatio, 1, 0.001);
    expect(result['relative_deviation_percent'], closeTo(0, 1e-10));
    expect(result['within_tolerance'], isTrue);
  });

  test('Length order does not affect ratio', () {
    expect(
      analyzePhi(1, 2, 2)['ratio_long_short'],
      analyzePhi(2, 1, 2)['ratio_long_short'],
    );
  });

  test('Equal lengths are not within two percent of phi', () {
    expect(analyzePhi(1, 1, 2)['within_tolerance'], isFalse);
  });

  test('Invalid inputs are rejected', () {
    expect(() => analyzePhi(0, 1, 2), throwsArgumentError);
    expect(() => analyzePhi(-1, 1, 2), throwsArgumentError);
    expect(() => analyzePhi(double.nan, 1, 2), throwsArgumentError);
    expect(() => analyzePhi(1, 2, -1), throwsArgumentError);
  });
}
