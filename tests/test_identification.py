from fossil_scanner.identification.character_matcher import match_candidate
from fossil_scanner.identification.identification_policy import decide_rank


def test_matcher_scores_supporting_and_contradictory():
    observed = [
        {"character_id": "c1", "state": "present", "observability": "visible"},
        {"character_id": "c2", "state": "absent", "observability": "visible"},
    ]
    rules = [
        {"character_id": "c1", "expected_states": ["present"], "weight": 2.0},
        {"character_id": "c2", "expected_states": ["present"], "weight": 1.0},
    ]
    result = match_candidate("t1", observed, rules)
    assert result["supporting"]
    assert result["contradictory"]
    assert result["score"] < 1.0


def test_policy_prefers_unresolved_without_evidence():
    decision = decide_rank({"observable_character_count": 0})
    assert decision["rank"] == "unresolved"


def test_policy_reviews_on_contradiction():
    decision = decide_rank({
        "observable_character_count": 3,
        "coverage": 0.5,
        "contradictory": [{"character_id": "x"}],
    })
    assert decision["rank"] == "review_required"
