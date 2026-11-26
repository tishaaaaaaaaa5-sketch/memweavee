"""Split-seed robustness analysis from notebook section 7."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .features import FEATURE_INDEX
from .inference import paired_bootstrap
from .modeling import fit_scores, make_folds
from .selection import recalls, selections
from .tuning import simple_scores, tune_pool


def evaluate_split_robustness(pools, question_records, valid_ids, *,
                              primary_pool="same_pipeline", seeds=range(11, 19),
                              test_fraction=0.5, folds=5, C_grid=(0.03, 0.3, 3.0),
                              budget=0.10, selection_options=None,
                              bootstrap_resamples=4000, bootstrap_seed=2):
    """Repeat dev tuning and locked-test evaluation on alternative stratified splits.

    Test halves overlap across seeds, so these rows are robustness diagnostics,
    not independent replications or a new confirmatory family.
    """
    labels = [question_records[q]["qtype"] for q in valid_ids]
    rows = []
    for seed in seeds:
        dev, test = train_test_split(
            list(valid_ids), test_size=test_fraction, stratify=labels, random_state=seed
        )
        dev, test = sorted(dev), sorted(test)
        fold_list = make_folds(dev, folds=folds, seed=seed)
        options = selection_options or (
            ("rank", 0.0), ("density", 0.0), ("mmr", 0.1),
            ("mmr", 0.25), ("mmr", 0.5),
        )
        tuned = tune_pool(
            pools, question_records, primary_pool, dev, fold_list,
            C_grid=C_grid, selection_options=options, budget=budget,
        )
        config = tuned["config"]
        scores, _, _ = fit_scores(
            pools, question_records, primary_pool, dev, test,
            config["C"], config["idx"],
        )
        learned = recalls(
            pools[primary_pool], test,
            selections(pools[primary_pool], test, scores, budget=budget,
                       mode=config["mode"], lam=config["lam"]),
        )
        simple = simple_scores(
            pools[primary_pool], dev,
            {name: FEATURE_INDEX[name] for name in ("rec_rank", "log_words", "mean_sim", "novelty")},
        )
        simple_means = {
            name: recalls(
                pools[primary_pool], dev,
                selections(pools[primary_pool], dev, score_map, budget=budget),
            ).mean()
            for name, score_map in simple.items()
        }
        best_simple = max(simple_means, key=simple_means.get)
        test_simple_scores = simple_scores(
            pools[primary_pool], test,
            {"rec_rank": 2, "log_words": 0, "mean_sim": 8, "novelty": 7},
        )[best_simple]
        baseline = recalls(
            pools[primary_pool], test,
            selections(pools[primary_pool], test, test_simple_scores, budget=budget),
        )
        comparison = paired_bootstrap(
            learned, baseline, resamples=bootstrap_resamples,
            seed=bootstrap_seed + int(seed),
        )
        rows.append({
            "split_seed": int(seed), "groups_kept": "+".join(config["groups"]),
            "best_simple": best_simple, "LR_recall": float(learned.mean()),
            "simple_recall": float(baseline.mean()), "diff": comparison["diff"],
            "ci_low": comparison["ci_low"], "ci_high": comparison["ci_high"],
            "n_dev": len(dev), "n_test": len(test),
        })
    return pd.DataFrame(rows)