"""Paired uncertainty and multiple-comparison helpers from the final notebook."""
from __future__ import annotations

import numpy as np


def bootstrap_mean(values, *, resamples: int = 4000, seed: int = 1):
    """Return mean and percentile 95% bootstrap interval (question-level resampling)."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("values must be a non-empty one-dimensional array")
    if resamples < 1:
        raise ValueError("resamples must be positive")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), (resamples, len(values)))
    means = values[indices].mean(1)
    return (
        float(values.mean()),
        float(np.percentile(means, 2.5)),
        float(np.percentile(means, 97.5)),
    )


def paired_bootstrap(
    treatment, control, *, resamples: int = 4000, seed: int = 2
) -> dict[str, float]:
    """Notebook-compatible paired difference, percentile CI and two-sided sign p-value."""
    treatment = np.asarray(treatment, dtype=float)
    control = np.asarray(control, dtype=float)
    if treatment.ndim != 1 or control.ndim != 1 or len(treatment) == 0:
        raise ValueError("paired inputs must be non-empty one-dimensional arrays")
    if len(treatment) != len(control):
        raise ValueError("paired inputs must have equal length")
    if resamples < 1:
        raise ValueError("resamples must be positive")
    difference = treatment - control
    rng = np.random.default_rng(seed)
    sampled = difference[rng.integers(0, len(difference), (resamples, len(difference)))].mean(1)
    p_value = min(
        1.0,
        max(2 * min((sampled <= 0).mean(), (sampled >= 0).mean()), 1.0 / resamples),
    )
    return {
        "diff": float(difference.mean()),
        "ci_low": float(np.percentile(sampled, 2.5)),
        "ci_high": float(np.percentile(sampled, 97.5)),
        "p": float(p_value),
    }


def holm_adjust(p_values) -> np.ndarray:
    """Holm step-down adjusted p-values, returned in original input order."""
    p_values = np.asarray(p_values, dtype=float)
    if p_values.ndim != 1 or np.any(~np.isfinite(p_values)):
        raise ValueError("p-values must be a finite one-dimensional array")
    if np.any((p_values < 0) | (p_values > 1)):
        raise ValueError("p-values must lie in [0, 1]")
    count = len(p_values)
    adjusted = np.empty(count, dtype=float)
    running = 0.0
    for rank, index in enumerate(np.argsort(p_values, kind="stable")):
        running = max(running, (count - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def classify_difference(
    result: dict[str, float],
    *,
    adjusted_p: float,
    equivalence_margin: float = 0.03,
    alpha: float = 0.05,
) -> str:
    """Apply the notebook's superiority/worse/equivalence/inconclusive rule."""
    if result["ci_low"] > 0 and adjusted_p < alpha:
        return "SUPERIOR"
    if result["ci_high"] < 0 and adjusted_p < alpha:
        return "WORSE"
    if result["ci_low"] >= -equivalence_margin and result["ci_high"] <= equivalence_margin:
        return f"EQUIVALENT (within +/-{equivalence_margin:.2f})"
    return "INCONCLUSIVE"
