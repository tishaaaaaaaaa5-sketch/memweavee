"""Locked-test reporting and secondary analyses from notebook sections 6–7.

The API accepts frozen development-selected configurations. It never performs
hyperparameter or selector tuning on the locked test questions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .inference import paired_bootstrap, holm_adjust, classify_difference
from .modeling import fit_scores
from .selection import recalls, selections, select_indices
from .tuning import simple_scores
from .features import feature_indices

PRIMARY_FAMILY = (
    "LR vs best simple rule (chosen on dev)",
    "LR vs recency",
    "LR vs random",
)


def compare_table(pairs, family, *, resamples=4000, seed=2, margin=0.03, alpha=0.05):
    """Build paired question-level comparisons with within-family Holm correction."""
    rows = [
        {"comparison": name, **paired_bootstrap(a, b, resamples=resamples, seed=seed + i)}
        for i, (name, a, b) in enumerate(pairs)
    ]
    adjusted = holm_adjust([row["p"] for row in rows])
    for row, p_value in zip(rows, adjusted):
        row["p_holm"] = float(p_value)
        row["verdict"] = classify_difference(
            row, adjusted_p=float(p_value), equivalence_margin=margin, alpha=alpha
        )
        row["family"] = family
    return pd.DataFrame(rows)


def _random_selections(pool_data, question_ids, *, budget, reps, seed):
    rng = np.random.default_rng(seed)
    output = {}
    for q in question_ids:
        item = pool_data[q]
        n = len(item["cost"])
        output[q] = [
            select_indices(rng.random(n), item["cost"], item["S"], budget)
            for _ in range(reps)
        ]
    return output


def _random_recalls(pool_data, question_ids, chosen):
    return np.asarray([
        np.mean([pool_data[q]["gold"][idx].sum() / pool_data[q]["gold"].sum()
                 for idx in chosen[q]]) if pool_data[q]["gold"].sum() else 0.0
        for q in question_ids
    ], dtype=float)


def _simple_scores(pool_data, question_ids):
    indices = {"rec_rank": 2, "log_words": 0, "mean_sim": 8, "novelty": 7}
    return simple_scores(pool_data, question_ids, indices)


def run_locked_evaluation(
    pools, question_records, dev_ids, test_ids, tuned, best_simple, *,
    primary_pool="same_pipeline", budget=0.10,
    budget_sweep=(0.05, 0.10, 0.20, 0.30),
    random_reps=50, random_seed=0, bootstrap_resamples=4000,
    bootstrap_seed=1, equivalence_margin=0.03, alpha=0.05,
):
    """Run frozen-config locked-test comparisons, ablations and mechanism tests.

    tuned and best_simple must come from development-only tuning. This function
    accepts no test labels for selecting model or selector configurations.
    """
    if not set(dev_ids).isdisjoint(test_ids):
        raise ValueError("development and locked-test question IDs must be disjoint")
    if primary_pool not in pools:
        raise ValueError(f"unknown primary pool: {primary_pool}")
    if random_reps < 1:
        raise ValueError("random_reps must be positive")
    results, selections_by_pool, score_by_pool = {}, {}, {}
    rows = []

    for pool, pool_data in pools.items():
        if pool not in tuned or pool not in best_simple:
            raise ValueError(f"missing frozen dev configuration for pool {pool!r}")
        config = tuned[pool]
        scores, kept, total = fit_scores(
            pools, question_records, pool, dev_ids, test_ids, config["C"], config["idx"]
        )
        all_indices = list(range(next(iter(pool_data.values()))["F"].shape[1]))
        all_scores, _, _ = fit_scores(
            pools, question_records, pool, dev_ids, test_ids, config["C"], all_indices
        )
        learned = selections(
            pool_data, test_ids, scores, budget=budget, mode=config["mode"], lam=config["lam"]
        )
        random_chosen = _random_selections(
            pool_data, test_ids, budget=budget, reps=random_reps, seed=random_seed
        )
        simple_score_map = _simple_scores(pool_data, test_ids)
        simple = {
            name: selections(pool_data, test_ids, simple_score_map[name], budget=budget)
            for name in ("recency", "longest", "high_centrality", "low_novelty")
        }
        results[pool] = {
            "random": _random_recalls(pool_data, test_ids, random_chosen),
            **{name: recalls(pool_data, test_ids, chosen) for name, chosen in simple.items()},
            "best_simple(dev-chosen)": recalls(pool_data, test_ids, simple[best_simple[pool]]),
            "LR (tuned)": recalls(pool_data, test_ids, learned),
            "LR (all groups)": recalls(
                pool_data, test_ids, selections(
                    pool_data, test_ids, all_scores, budget=budget,
                    mode=config["mode"], lam=config["lam"],
                )
            ),
        }
        selections_by_pool[pool] = {"lr": learned, "random": random_chosen, "simple": simple}
        score_by_pool[pool] = scores
        for method, values in results[pool].items():
            mean, low, high = _bootstrap_summary(
                values, resamples=bootstrap_resamples, seed=bootstrap_seed
            )
            rows.append((pool, method, mean, low, high, len(values), kept, total))

    main = pd.DataFrame(rows, columns=[
        "pool", "method", "recall@budget", "ci_low", "ci_high",
        "n_test_questions", "training_rows_kept", "training_rows_total",
    ])
    primary = results[primary_pool]
    confirmatory = compare_table([
        (PRIMARY_FAMILY[0], primary["LR (tuned)"], primary["best_simple(dev-chosen)"]),
        (PRIMARY_FAMILY[1], primary["LR (tuned)"], primary["recency"]),
        (PRIMARY_FAMILY[2], primary["LR (tuned)"], primary["random"]),
    ], "PRIMARY (confirmatory)", resamples=bootstrap_resamples,
       seed=bootstrap_seed + 10, margin=equivalence_margin, alpha=alpha)
    confirmatory.insert(0, "pool", primary_pool)
    descriptive = []
    for pool in pools:
        if pool == primary_pool:
            continue
        table = compare_table([
            ("LR vs best simple rule (chosen on dev)",
             results[pool]["LR (tuned)"], results[pool]["best_simple(dev-chosen)"]),
            ("LR vs random", results[pool]["LR (tuned)"], results[pool]["random"]),
        ], "descriptive", resamples=bootstrap_resamples,
           seed=bootstrap_seed + 20, margin=equivalence_margin, alpha=alpha)
        table.insert(0, "pool", pool)
        descriptive.append(table)
    comparisons = pd.concat([confirmatory, *descriptive], ignore_index=True)

    config = tuned[primary_pool]
    full = results[primary_pool]["LR (tuned)"]
    ablation_pairs = []
    groups = list(config["groups"])
    for removed in groups if len(groups) > 1 else []:
        indices = feature_indices([g for g in groups if g != removed])
        ablation_scores, _, _ = fit_scores(
            pools, question_records, primary_pool, dev_ids, test_ids, config["C"], indices
        )
        ablated = recalls(
            pools[primary_pool], test_ids, selections(
                pools[primary_pool], test_ids, ablation_scores, budget=budget,
                mode=config["mode"], lam=config["lam"],
            )
        )
        ablation_pairs.append((f"remove group: {removed}", full, ablated))
    ablation = compare_table(
        ablation_pairs, "ablation", resamples=bootstrap_resamples,
        seed=bootstrap_seed + 30, margin=equivalence_margin, alpha=alpha,
    ) if ablation_pairs else pd.DataFrame()
    if not ablation.empty:
        ablation["contributes"] = np.where(
            (ablation["ci_low"] > 0) & (ablation["p_holm"] < alpha),
            "YES (group helps)",
            np.where((ablation["ci_high"] < 0) & (ablation["p_holm"] < alpha),
                     "NO (removing it improves recall)", "no reliable contribution"),
        )

    rank = recalls(
        pools[primary_pool], test_ids, selections(
            pools[primary_pool], test_ids, score_by_pool[primary_pool],
            budget=budget, mode="rank",
        )
    )
    mechanism_pairs = []
    for mode, penalty in (("density", 0.0), ("mmr", 0.25), ("mmr", 0.5)):
        forced = recalls(
            pools[primary_pool], test_ids, selections(
                pools[primary_pool], test_ids, score_by_pool[primary_pool],
                budget=budget, mode=mode, lam=penalty,
            )
        )
        suffix = f" lambda={penalty}" if mode == "mmr" else ""
        mechanism_pairs.append((f"{mode}{suffix} minus rank", forced, rank))
    mechanism = compare_table(
        mechanism_pairs, "mechanism", resamples=bootstrap_resamples,
        seed=bootstrap_seed + 40, margin=equivalence_margin, alpha=alpha,
    )

    sweep_pairs = []
    baseline_scores = _simple_scores(pools[primary_pool], test_ids)[best_simple[primary_pool]]
    for fraction in budget_sweep:
        learned = recalls(
            pools[primary_pool], test_ids, selections(
                pools[primary_pool], test_ids, score_by_pool[primary_pool],
                budget=fraction, mode=config["mode"], lam=config["lam"],
            )
        )
        baseline = recalls(
            pools[primary_pool], test_ids, selections(
                pools[primary_pool], test_ids, baseline_scores, budget=fraction,
            )
        )
        sweep_pairs.append((f"budget {int(fraction * 100)}%: LR minus {best_simple[primary_pool]}",
                            learned, baseline))
    sweep = compare_table(
        sweep_pairs, "budget sweep", resamples=bootstrap_resamples,
        seed=bootstrap_seed + 50, margin=equivalence_margin, alpha=alpha,
    )
    return {
        "results": results, "selections": selections_by_pool, "scores": score_by_pool,
        "main_results": main, "comparisons": comparisons,
        "group_ablation": ablation, "mechanism_test": mechanism, "budget_sweep": sweep,
    }


def _bootstrap_summary(values, *, resamples, seed):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("values must be a non-empty one-dimensional array")
    if resamples < 1:
        raise ValueError("resamples must be positive")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), (resamples, len(values)))
    sampled = values[indices].mean(1)
    return (float(values.mean()), float(np.percentile(sampled, 2.5)),
            float(np.percentile(sampled, 97.5)))