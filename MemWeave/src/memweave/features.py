"""Leak-aware feature construction extracted from the final evaluation notebook.

Inputs are one question's candidate-session vectors and metadata. All
normalisation is within that question's candidate pool, matching the notebook.
"""
from __future__ import annotations

import numpy as np

FEATURES = (
    "log_words", "n_turns", "rec_rank", "log_days_before", "user_frac",
    "first_person", "digit_rate", "novelty", "mean_sim", "top3_sim",
)
GROUPS = {
    "length": ("log_words", "n_turns"),
    "time": ("rec_rank", "log_days_before"),
    "style": ("user_frac", "first_person", "digit_rate"),
    "similarity": ("novelty", "mean_sim", "top3_sim"),
}
FEATURE_INDEX = {name: index for index, name in enumerate(FEATURES)}


def zscore(matrix: np.ndarray) -> np.ndarray:
    """Column-standardise a matrix using the notebook's 1e-6 stabiliser."""
    matrix = np.asarray(matrix)
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    return (matrix - matrix.mean(0, keepdims=True)) / (
        matrix.std(0, keepdims=True) + 1e-6
    )


def build_features(
    vectors,
    words,
    user_words,
    turns,
    first_person_rate,
    digit_rate,
    days,
    question_day,
) -> tuple[np.ndarray, np.ndarray]:
    """Return z-scored candidate features and the pairwise cosine-similarity matrix.

    `vectors` must contain L2-normalised rows, as in the notebook's TF-IDF
    representation. Sparse matrices are accepted.
    """
    n = vectors.shape[0]
    if n == 0:
        raise ValueError("at least one candidate session is required")
    arrays = [np.asarray(x) for x in (
        words, user_words, turns, first_person_rate, digit_rate, days
    )]
    if any(a.ndim != 1 or len(a) != n for a in arrays):
        raise ValueError("each metadata vector must be one-dimensional and match candidates")
    words, user_words, turns, first_person_rate, digit_rate, days = arrays

    similarities = vectors @ vectors.T
    if hasattr(similarities, "toarray"):
        similarities = similarities.toarray()
    similarities = np.asarray(similarities, dtype=np.float32)
    np.fill_diagonal(similarities, 0.0)
    maximum = similarities.max(1) if n > 1 else np.zeros(n)
    sorted_similarities = np.sort(similarities, 1)
    top3 = (
        sorted_similarities[:, -min(3, n - 1):].mean(1)
        if n > 1 else np.zeros(n)
    )
    order = np.argsort(np.argsort(days, kind="stable"), kind="stable")
    raw = np.column_stack([
        np.log1p(words),
        turns,
        order / max(n - 1, 1),
        np.log1p(np.clip(question_day - days, 0, None))
        if question_day is not None else np.zeros(n),
        user_words / np.maximum(words, 1),
        first_person_rate,
        digit_rate,
        1.0 - maximum,
        similarities.sum(1) / max(n - 1, 1),
        top3,
    ])
    return zscore(raw).astype(np.float32), similarities


def feature_indices(groups: list[str] | tuple[str, ...]) -> list[int]:
    """Resolve notebook feature groups into the original stable column order."""
    unknown = set(groups) - set(GROUPS)
    if unknown:
        raise ValueError(f"unknown feature groups: {sorted(unknown)}")
    selected = {name for group in groups for name in GROUPS[group]}
    return [FEATURE_INDEX[name] for name in FEATURES if name in selected]


def pool_rows(question: dict, pool: str) -> list[dict]:
    """Apply the notebook's three pre-defined candidate-pool definitions."""
    if pool == "all":
        return list(question["rows"])
    if pool == "same_pipeline":
        keep = ("gold", "generated")
    elif pool == "filler":
        keep = ("gold", "filler")
    else:
        raise ValueError(f"unknown candidate pool: {pool}")
    return [row for row in question["rows"] if row["kind"] in keep]
