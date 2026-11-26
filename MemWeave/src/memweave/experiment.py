"""Question-pool construction and leakage-controlled LongMemEval split helpers."""
from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

from .features import build_features, pool_rows

POOLS = ("same_pipeline", "all", "filler")


def build_question_pools(questions, sessions, session_matrix):
    """Reproduce the notebook's per-question feature matrices and three pools."""
    pools = {name: {} for name in POOLS}
    for question_index, question in enumerate(questions):
        if question["is_abs"]:
            continue
        for pool_name in POOLS:
            rows = pool_rows(question, pool_name)
            gold = np.asarray([row["gold"] for row in rows], dtype=bool)
            if len(rows) < 3 or gold.all() or not gold.any():
                continue
            indices = np.asarray([row["h"] for row in rows], dtype=int)
            days = np.asarray([row["day"] for row in rows], dtype=float)
            features, similarity = build_features(
                session_matrix[indices], sessions["words"][indices],
                sessions["user"][indices], sessions["turns"][indices],
                sessions["fp"][indices], sessions["digit"][indices],
                days, question["qday"],
            )
            pools[pool_name][question_index] = {
                "h": indices, "F": features, "S": similarity, "gold": gold,
                "cost": sessions["words"][indices].astype(float),
            }
    return pools


def locked_split(pools, questions, *, test_fraction=0.5, seed=2026):
    """Create the stratified split over questions valid in every candidate pool."""
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    valid = sorted(set.intersection(*(set(pools[name]) for name in POOLS)))
    if not valid:
        raise ValueError("no questions are valid in all candidate pools")
    labels = [questions[index]["qtype"] for index in valid]
    dev, test = train_test_split(
        valid, test_size=test_fraction, stratify=labels, random_state=seed
    )
    return {
        "valid": valid, "dev": sorted(dev), "test": sorted(test),
        "question_types": labels,
    }
