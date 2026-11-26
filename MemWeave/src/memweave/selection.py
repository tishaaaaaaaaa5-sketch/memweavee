"""Budget-constrained evidence selection extracted from the final notebook."""
from __future__ import annotations

import numpy as np


def select_indices(
    scores,
    costs,
    similarities,
    budget: float,
    *,
    mode: str = "rank",
    redundancy_penalty: float = 0.0,
) -> np.ndarray:
    """Select candidates under a fraction-of-total-cost budget.

    Modes preserve notebook semantics: stable score ranking, score/cost
    density, or greedy maximal-marginal-relevance (MMR).
    """
    scores = np.asarray(scores, dtype=float)
    costs = np.asarray(costs, dtype=float)
    similarities = np.asarray(similarities, dtype=float)
    if scores.ndim != 1 or costs.ndim != 1 or len(scores) != len(costs):
        raise ValueError("scores and costs must be equal-length one-dimensional arrays")
    n = len(scores)
    if similarities.shape != (n, n):
        raise ValueError("similarities must be a square matrix matching candidates")
    if not 0 <= budget <= 1:
        raise ValueError("budget must be between 0 and 1")
    if np.any(costs < 0) or not np.all(np.isfinite(costs)):
        raise ValueError("costs must be finite and non-negative")
    if not np.all(np.isfinite(scores)) or not np.all(np.isfinite(similarities)):
        raise ValueError("scores and similarities must be finite")
    if mode not in {"rank", "density", "mmr"}:
        raise ValueError(f"unknown selection mode: {mode}")

    limit = budget * costs.sum()
    chosen: list[int] = []
    used = 0.0
    if mode == "mmr":
        available = set(range(n))
        max_similarity = np.zeros(n)
        while available:
            best, best_value = None, -1e18
            for index in sorted(available):
                if used + costs[index] > limit:
                    continue
                value = scores[index] - redundancy_penalty * max_similarity[index]
                if value > best_value:
                    best_value, best = value, index
            if best is None:
                break
            chosen.append(best)
            used += costs[best]
            available.remove(best)
            max_similarity = np.maximum(max_similarity, similarities[best])
        return np.asarray(chosen, dtype=int)

    key = scores if mode == "rank" else scores / np.maximum(costs, 1.0)
    for index in np.argsort(-key, kind="stable"):
        if used + costs[index] <= limit:
            chosen.append(int(index))
            used += costs[index]
    return np.asarray(chosen, dtype=int)


def evidence_recall(relevant, selected_indices) -> float:
    """Fraction of relevant candidates retained by a selected index array."""
    relevant = np.asarray(relevant, dtype=bool)
    selected_indices = np.asarray(selected_indices, dtype=int)
    if relevant.ndim != 1:
        raise ValueError("relevant must be one-dimensional")
    if selected_indices.ndim != 1 or np.any(selected_indices < 0) or np.any(selected_indices >= len(relevant)):
        raise ValueError("selected indices are out of range")
    denominator = int(relevant.sum())
    return float(relevant[selected_indices].sum() / denominator) if denominator else 0.0


def recall_of(question_data: dict, chosen) -> float:
    """Evidence recall for one question's selected candidate indices."""
    gold = np.asarray(question_data["gold"], dtype=bool)
    chosen = np.asarray(chosen, dtype=int)
    return float(gold[chosen].sum() / gold.sum()) if gold.sum() else 0.0


def selections(pools, question_ids, scores, *, budget=0.10, mode="rank", lam=0.0):
    """Apply a selection policy independently to each question in a pool mapping."""
    return {
        question_id: select_indices(
            scores[question_id], pools[question_id]["cost"], pools[question_id]["S"],
            budget, mode=mode, redundancy_penalty=lam,
        )
        for question_id in question_ids
    }


def recalls(pools, question_ids, selected) -> np.ndarray:
    """Return one evidence-recall value per question, preserving question order."""
    return np.asarray([
        recall_of(pools[question_id], selected[question_id])
        for question_id in question_ids
    ], dtype=float)
