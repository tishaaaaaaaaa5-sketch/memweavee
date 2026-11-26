"""Leakage-aware model fitting and development-only cross-validation."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from .selection import recalls, selections


def stack_questions(pools, question_ids, feature_indices):
    """Stack candidate rows and preserve deduplicated session indices."""
    if not question_ids:
        raise ValueError("at least one question is required")
    x = np.vstack([pools[q]["F"][:, feature_indices] for q in question_ids])
    y = np.concatenate([pools[q]["gold"] for q in question_ids]).astype(int)
    hashes = np.concatenate([pools[q]["h"] for q in question_ids])
    return x, y, hashes


def make_model(kind="lr", C=0.3):
    """Instantiate the notebook's fixed LR or HGB classifier."""
    if kind == "hgb":
        return HistGradientBoostingClassifier(
            max_depth=3, max_iter=120, learning_rate=0.08, random_state=0
        )
    if kind != "lr":
        raise ValueError(f"unknown model kind: {kind}")
    return LogisticRegression(C=C, class_weight="balanced", max_iter=500)


def fit_scores(pools, question_records, pool, train_ids, test_ids, C,
               feature_indices, kind="lr"):
    """Fit after excluding training sessions that occur in held-out questions."""
    if not train_ids or not test_ids:
        raise ValueError("train_ids and test_ids must both be non-empty")
    held_out = set().union(*(question_records[q]["all_hashes"] for q in test_ids))
    x_train, y_train, train_hashes = stack_questions(
        pools[pool], train_ids, feature_indices
    )
    keep = ~np.isin(train_hashes, np.fromiter(held_out, dtype=np.int64))
    if not keep.any():
        raise ValueError("content de-duplication removed every training row")
    if np.unique(y_train[keep]).size < 2:
        raise ValueError("training rows must contain both classes after de-duplication")
    model = make_model(kind, C).fit(x_train[keep], y_train[keep])
    predictions = {
        q: model.predict_proba(pools[pool][q]["F"][:, feature_indices])[:, 1]
        for q in test_ids
    }
    return predictions, int(keep.sum()), int(len(keep))


def make_folds(question_ids, *, folds=5, seed=2026):
    """Create deterministic shuffled folds using the notebook's permutation rule."""
    if folds < 2 or folds > len(question_ids):
        raise ValueError("folds must be between 2 and the number of questions")
    permutation = np.random.default_rng(seed).permutation(question_ids)
    return [sorted(part.tolist()) for part in np.array_split(permutation, folds)]


def out_of_fold_scores(pools, question_records, pool, folds, C, feature_indices):
    """Generate OOF predictions, applying content-overlap filtering in every fold."""
    output = {}
    for fold_index, test_fold in enumerate(folds):
        train_fold = [
            question for index, fold in enumerate(folds) if index != fold_index
            for question in fold
        ]
        scores, _, _ = fit_scores(
            pools, question_records, pool, train_fold, test_fold, C, feature_indices
        )
        output.update(scores)
    expected = {question for fold in folds for question in fold}
    if set(output) != expected:
        raise RuntimeError("out-of-fold predictions do not cover each dev question exactly once")
    return output


def cv_recall(pools, question_records, pool, question_ids, folds, C,
              feature_indices, *, budget=0.10, mode="rank", lam=0.0):
    """Mean question-level OOF evidence recall at the specified retention budget."""
    scores = out_of_fold_scores(
        pools, question_records, pool, folds, C, feature_indices
    )
    chosen = selections(
        pools[pool], question_ids, scores, budget=budget, mode=mode, lam=lam
    )
    return float(recalls(pools[pool], question_ids, chosen).mean())
