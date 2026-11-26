import pytest
from memweave.metrics import paired_gain, recall_at_budget

def test_paired_gain():
    assert paired_gain([0.2, 0.4], [0.3, 0.8]) == pytest.approx(0.25)

def test_paired_gain_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        paired_gain([], [])
    with pytest.raises(ValueError):
        paired_gain([1], [1, 2])

def test_recall_at_budget():
    assert recall_at_budget({"a", "b", "c"}, {"b", "c", "x"}) == pytest.approx(2 / 3)

def test_recall_requires_relevant_evidence():
    with pytest.raises(ValueError):
        recall_at_budget(set(), {"a"})
