"""Development-only hyperparameter and selector tuning from notebook section 5."""
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
    """Build the four label-free notebook heuristics from feature columns."""
    definitions = {
        "recency": lambda f: f[:, feature_indices["rec_rank"]],
        "longest": lambda f: f[:, feature_indices["log_words"]],
        "high_centrality": lambda f: f[:, feature_indices["mean_sim"]],
        "low_novelty": lambda f: -f[:, feature_indices["novelty"]],
    }
    return {
        name: {
            question: score_fn(pool_data[question]["F"])
            for question in question_ids
        }
        for name, score_fn in definitions.items()
    }


def tune_pool(
    pools, question_records, pool, dev_ids, folds, *,
    C_grid=(0.03, 0.3, 3.0), groups=GROUPS,
    feature_order=FEATURES, selection_options=(
        ("rank", 0.0), ("density", 0.0), ("mmr", 0.1),
        ("mmr", 0.25), ("mmr", 0.5),
    ), budget=0.10,
):
    """Run the notebook's LR C search, backward group elimination, and 1-SE selector rule.

    All choices are made using only the supplied development questions and OOF
    predictions. The returned configuration can then be frozen before test use.
    """
    if not C_grid:
        raise ValueError("C_grid must not be empty")
    if not selection_options:
        raise ValueError("selection_options must not be empty")
    feature_index = {name: index for index, name in enumerate(feature_order)}
    group_map = {name: tuple(values) for name, values in groups.items()}
    group_list = list(group_map)
    tune_rows = []

    cv_by_c = {
        C: cv_recall(
            pools, question_records, pool, dev_ids, folds, C,
            list(range(len(feature_order))), budget=budget,
        )
        for C in C_grid
    }
    best_c = max(cv_by_c, key=cv_by_c.get)
    for C, value in cv_by_c.items():
        tune_rows.append((pool, "C", C, value, np.nan))

    retained = list(group_list)
    current = cv_recall(
        pools, question_records, pool, dev_ids, folds, best_c,
        group_indices(retained, group_map, feature_order), budget=budget,
    )
    while len(retained) > 1:
        trials = [
            (
                cv_recall(
                    pools, question_records, pool, dev_ids, folds, best_c,
                    group_indices([name for name in retained if name != group],
                                  group_map, feature_order),
                    budget=budget,
                ),
                group,
            )
            for group in retained
        ]
        trial_score, removed = max(trials)
        if trial_score >= current:
            retained.remove(removed)
            current = trial_score
            tune_rows.append((pool, "group_removed", removed, trial_score, np.nan))
        else:
            break

    selected_features = group_indices(retained, group_map, feature_order)
    oof = out_of_fold_scores(
        pools, question_records, pool, folds, best_c, selected_features
    )
    option_stats = []
    for mode, penalty in selection_options:
        values = recalls(
            pools[pool], dev_ids,
            selections(pools[pool], dev_ids, oof, budget=budget,
                       mode=mode, lam=penalty),
        )
        standard_error = values.std(ddof=1) / np.sqrt(len(values)) if len(values) > 1 else 0.0
        option_stats.append((mode, penalty, float(values.mean()), float(standard_error)))

    best_mean = max(item[2] for item in option_stats)
    best_se = next(item[3] for item in option_stats if item[2] == best_mean)
    chosen = next(item for item in option_stats if item[2] >= best_mean - best_se)
    for mode, penalty, mean, standard_error in option_stats:
        tune_rows.append((pool, f"selection:{mode}", penalty, mean, standard_error))

    simple = simple_scores(
        pools[pool], dev_ids,
        {name: feature_index[name] for name in
         ("rec_rank", "log_words", "mean_sim", "novelty")},
    )
    simple_means = {
        name: float(recalls(
            pools[pool], dev_ids,
            selections(pools[pool], dev_ids, scores, budget=budget),
        ).mean())
        for name, scores in simple.items()
    }
    best_simple = max(simple_means, key=simple_means.get)
    tune_rows.extend(
        (pool, "simple_rule", name, value, np.nan)
        for name, value in simple_means.items()
    )

    return {
        "config": {
            "C": best_c, "mode": chosen[0], "lam": chosen[1],
            "groups": retained, "idx": selected_features,
        },
        "best_simple": best_simple,
        "tune_rows": tune_rows,
        "cv_by_C": cv_by_c,
        "selection_cv": option_stats,
        "simple_cv": simple_means,
    }
