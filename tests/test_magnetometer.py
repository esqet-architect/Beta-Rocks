from fossil_scanner.magnetometer import process_magnetic_samples, anomaly_classification


def test_empty_samples_yield_none_fields():
    result = process_magnetic_samples([])
    assert result["count"] == 0
    assert result["magnitude"]["median_uT"] is None
    assert result["vector_mean"]["x_uT"] is None


def test_nonempty_samples_compute():
    samples = [{"x": 1.0, "y": 0.0, "z": 0.0}, {"x": 0.0, "y": 2.0, "z": 0.0}]
    result = process_magnetic_samples(samples)
    assert result["count"] == 2
    assert result["vector_mean"]["x_uT"] == 0.5


def test_anomaly_indeterminate_without_baseline():
    result = anomaly_classification(5.0, None, None)
    assert result["classification"] == "indeterminate"


def test_anomaly_none_when_within_threshold():
    result = anomaly_classification(5.0, 5.0, 1.0)
    assert result["classification"] == "none"


def test_anomaly_positive():
    result = anomaly_classification(10.0, 5.0, 1.0)
    assert result["classification"] == "positive_anomaly"
