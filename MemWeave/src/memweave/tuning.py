"""Development-only hyperparameter and selector tuning."""
from __future__ import annotations

import numpy as np

from .features import FEATURES, GROUPS
from .modeling import cv_recall, out_of_fold_scores
from .selection import recalls, selections


def group_indices(groups_to_keep, group_map=GROUPS, feature_order=FEATURES):
    """Resolve retained feature groups in the notebook's canonical column order."""
    unknown = set(groups_to_keep) - set(group_map)
    if unknown:
        raise ValueError(f"unknown feature groups: {sorted(unknown)}")
    selected = {feature for group in groups_to_keep for feature in group_map[group]}
    return [index for index, feature in enumerate(feature_order) if feature in selected]


def simple_scores(pool_data, question_ids, feature_indices):
    """Build the four label-free heuristics from feature columns."""
    definitions = {
        "recency": lambda f: f[:, feature_indices["rec_rank"]],
        "longest": lambda f: f[:, feature_indices["log_words"]],
        "high_centrality": lambda f: f[:, feature_indices["mean_sim"]],
        "low_novelty": lambda f: -f[:, feature_indices["novelty"]],
    }
    return {
        name: {q: fn(pool_data[q]["F"]) for q in question_ids}
        for name, fn in definitions.items()
    }


def tune_pool(pools, question_records, pool, dev_ids, folds, *,
              C_grid=(0.03, 0.3, 3.0), groups=GROUPS,
              selection_options=(("rank", 0.0), ("density", 0.0),
                                 ("mmr", 0.1), ("mmr", 0.25), ("mmr", 0.5)),
              budget=0.10):
    """Tune C, feature groups, selector and simple baseline using dev OOF scores only."""
    if not C_grid or not selection_options:
        raise ValueError("C_grid and selection_options must not be empty")
    group_map = {name: tuple(columns) for name, columns in groups.items()}
    all_indices = list(range(len(FEATURES)))
    rows = []
    cv_by_c = {
        C: cv_recall(
            pools, question_records, pool, dev_ids, folds, C, all_indices,
            budget=budget,
        )
        for C in C_grid
    }
    best_c = max(C_grid, key=lambda value: cv_by_c[value])
    rows.extend((pool, "C", C, score, np.nan) for C, score in cv_by_c.items())

    retained = list(group_map)
    current = cv_recall(
        pools, question_records, pool, dev_ids, folds, best_c,
        group_indices(retained, group_map), budget=budget,
    )
    while len(retained) > 1:
        trials = [
            (cv_recall(
                pools, question_records, pool, dev_ids, folds, best_c,
                group_indices([g for g in retained if g != removed], group_map),
                budget=budget,
            ), removed)
            for removed in retained
        ]
        trial_score, removed = max(trials)
        if trial_score < current:
            break
        retained.remove(removed)
        current = trial_score
        rows.append((pool, "group_removed", removed, trial_score, np.nan))

    indices = group_indices(retained, group_map)
    oof = out_of_fold_scores(
        pools, question_records, pool, folds, best_c, indices
    )
    option_stats = []
    for mode, penalty in selection_options:
        values = recalls(
            pools[pool], dev_ids,
            selections(pools[pool], dev_ids, oof, budget=budget,
                       mode=mode, lam=penalty),
        )
        se = values.std(ddof=1) / np.sqrt(len(values)) if len(values) > 1 else 0.0
        option_stats.append((mode, penalty, float(values.mean()), float(se)))

    best = max(item[2] for item in option_stats)
    best_se = next(item[3] for item in option_stats if item[2] == best)
    # Input order is the pre-declared simplicity order: rank, density, then MMR.
    chosen = next(item for item in option_stats if item[2] >= best - best_se)
    rows.extend(
        (pool, f"selection:{mode}", penalty, mean, se)
        for mode, penalty, mean, se in option_stats
    )

    index = {name: i for i, name in enumerate(FEATURES)}
    simple = simple_scores(
        pools[pool], dev_ids,
        {name: index[name] for name in ("rec_rank", "log_words", "mean_sim", "novelty")},
    )
    simple_means = {
        name: float(recalls(
            pools[pool], dev_ids,
            selections(pools[pool], dev_ids, scores, budget=budget),
        ).mean())
        for name, scores in simple.items()
    }
    best_simple = max(simple_means, key=simple_means.get)
    rows.extend((pool, "simple_rule", name, score, np.nan)
                for name, score in simple_means.items())
    return {
        "config": {"C": best_c, "mode": chosen[0], "lam": chosen[1],
                   "groups": retained, "idx": indices},
        "best_simple": best_simple, "tune_rows": rows,
        "cv_by_C": cv_by_c, "selection_cv": option_stats,
        "simple_cv": simple_means,
    }
