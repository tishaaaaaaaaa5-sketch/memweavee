"""Small, dependency-light metric helpers."""
from collections.abc import Sequence

def paired_gain(baseline: Sequence[float], treatment: Sequence[float]) -> float:
    """Return mean paired treatment-minus-baseline gain."""
    if not baseline or not treatment:
        raise ValueError("paired inputs must be non-empty")
    if len(baseline) != len(treatment):
        raise ValueError("paired inputs must have equal length")
    return sum(float(y) - float(x) for x, y in zip(baseline, treatment)) / len(baseline)

def recall_at_budget(relevant: set[str], retained: set[str]) -> float:
    """Compute set-based evidence recall."""
    if not relevant:
        raise ValueError("relevant evidence set must be non-empty")
    return len(relevant & retained) / len(relevant)
