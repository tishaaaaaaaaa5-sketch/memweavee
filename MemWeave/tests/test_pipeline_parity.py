"""Synthetic parity fixtures for the extracted final-notebook primitives."""
import numpy as np
import pytest

from memweave.features import build_features, feature_indices, pool_rows
from memweave.inference import classify_difference, holm_adjust, paired_bootstrap
from memweave.selection import evidence_recall, select_indices


def test_pool_definitions_match_notebook():
    question = {"rows": [
        {"id": "a", "kind": "gold"}, {"id": "b", "kind": "generated"},
        {"id": "c", "kind": "filler"},
    ]}
    assert [r["id"] for r in pool_rows(question, "same_pipeline")] == ["a", "b"]
    assert [r["id"] for r in pool_rows(question, "filler")] == ["a", "c"]
    assert len(pool_rows(question, "all")) == 3


def test_feature_group_column_order_is_stable():
    assert feature_indices(["similarity", "length"]) == [0, 1, 7, 8, 9]
    assert feature_indices(["style", "time"]) == [2, 3, 4, 5, 6]


def test_feature_builder_shapes_and_poolwise_standardisation():
    vectors = np.array([[1., 0.], [0., 1.], [1., 1.]])
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    features, similarity = build_features(
        vectors, [10, 20, 30], [5, 10, 15], [2, 3, 4],
        [0.1, 0.2, 0.3], [0.0, 0.1, 0.2], [1., 2., 3.], 4.,
    )
    assert features.shape == (3, 10)
    assert similarity.shape == (3, 3)
    assert np.allclose(np.diag(similarity), 0)
    assert np.allclose(features.mean(0), 0, atol=1e-6)
    assert np.all(np.isfinite(features))


def test_feature_builder_single_candidate_is_finite():
    features, similarity = build_features(
        np.array([[1., 0.]]), [4], [2], [1], [0.0], [0.0], [1.], None
    )
    assert features.shape == (1, 10)
    assert similarity.shape == (1, 1)
    assert np.all(np.isfinite(features))


@pytest.mark.parametrize("mode,expected", [
    ("rank", [0]), ("density", [1]), ("mmr", [0, 2]),
])
def test_budget_selection_matches_greedy_rules(mode, expected):
    scores = np.array([0.9, 0.8, 0.7])
    costs = np.array([2., 1., 1.])
    similarity = np.array([[0., .9, .1], [.9, 0., .1], [.1, .1, 0.]])
    selected = select_indices(
        scores, costs, similarity, .5, mode=mode, redundancy_penalty=.5
    )
    assert selected.tolist() == expected


def test_evidence_recall_and_zero_evidence():
    assert evidence_recall([True, False, True], [0, 1]) == .5
    assert evidence_recall([False, False], [0]) == 0.0


def test_holm_adjustment_preserves_original_order():
    assert np.allclose(holm_adjust([.01, .04, .03]), [.03, .06, .06])


def test_paired_bootstrap_is_deterministic_and_classifies():
    a = [0.8, 0.7, 0.9, 0.6]
    b = [0.4, 0.5, 0.6, 0.3]
    result = paired_bootstrap(a, b, resamples=500, seed=9)
    assert result == paired_bootstrap(a, b, resamples=500, seed=9)
    assert result["diff"] == pytest.approx(.3)
    assert classify_difference(result, adjusted_p=.01) == "SUPERIOR"


def test_invalid_selection_mode_is_rejected():
    with pytest.raises(ValueError, match="unknown selection mode"):
        select_indices([1], [1], [[0]], .5, mode="mystery")
