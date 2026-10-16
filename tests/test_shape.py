from fossil_scanner.analysis.shape import (
    describe_shape, fold_angle, endpoint_proximity, bilateral_similarity,
)


def test_describe_returns_expected_keys():
    points = [(0, 0), (1, 1), (2, 0), (3, 1), (4, 0)]
    result = describe_shape(points)
    assert "fold_angle_deg" in result
    assert "endpoint_proximity" in result
    assert "bilateral_similarity" in result


def test_endpoint_proximity_detects_closed_fold():
    points = [(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1), (0, 0.5)]
    result = endpoint_proximity(points)
    assert result["status"] == "ok"
    assert result["end_gap_fraction"] >= 0.0


def test_bilateral_similarity_symmetric_shape():
    points = [(-1, 0), (-0.5, 1), (0, 2), (0.5, 1), (1, 0)]
    result = bilateral_similarity(points)
    assert result["status"] == "ok"
    assert 0.0 <= result["symmetry_score"] <= 1.0
