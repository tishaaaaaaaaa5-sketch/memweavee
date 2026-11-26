import numpy as np

from memweave.features import FEATURES
from memweave.modeling import make_folds, out_of_fold_scores, fit_scores
from memweave.tuning import tune_pool
from memweave.evaluation import run_locked_evaluation


def fixture():
    rng = np.random.default_rng(42)
    pool = {name: {} for name in ("same_pipeline", "all", "filler")}
    records = []
    for q in range(12):
        x = rng.normal(size=(4, len(FEATURES)))
        x[0, 0] += 1.5
        x[:, 2] += np.linspace(0, 1, 4)
        item = {
            "F": x, "gold": np.array([True, False, False, False]),
            "h": np.arange(q * 4, q * 4 + 4), "cost": np.ones(4),
            "S": np.eye(4),
        }
        for name in pool:
            pool[name][q] = item
        records.append({"all_hashes": set(range(q * 4, q * 4 + 4))})
    return pool, records


def test_oof_scoring_covers_dev_questions_and_excludes_heldout_hashes():
    pools, records = fixture()
    folds = make_folds(list(range(8)), folds=2, seed=17)
    scores = out_of_fold_scores(pools, records, "same_pipeline", folds, .3, list(range(10)))
    assert set(scores) == set(range(8))
    test_scores, kept, total = fit_scores(
        pools, records, "same_pipeline", list(range(8)), [8, 9, 10, 11],
        .3, list(range(10)),
    )
    assert set(test_scores) == {8, 9, 10, 11}
    assert kept == total == 32


def test_tuning_uses_dev_oof_and_returns_frozen_config():
    pools, records = fixture()
    dev = list(range(8))
    folds = make_folds(dev, folds=2, seed=17)
    tuned = tune_pool(
        pools, records, "same_pipeline", dev, folds, C_grid=[.3],
        selection_options=[("rank", 0.0)], budget=.5,
    )
    assert tuned["config"]["C"] == .3
    assert tuned["config"]["mode"] == "rank"
    assert set(tuned["config"]["idx"]) <= set(range(10))
    assert tuned["best_simple"] in {"recency", "longest", "high_centrality", "low_novelty"}


def test_locked_evaluation_reports_only_disjoint_test_questions():
    pools, records = fixture()
    dev, test = list(range(8)), list(range(8, 12))
    folds = make_folds(dev, folds=2, seed=17)
    tuned = {}
    best_simple = {}
    for name in pools:
        result = tune_pool(
            pools, records, name, dev, folds, C_grid=[.3],
            selection_options=[("rank", 0.0)], budget=.5,
        )
        tuned[name] = result["config"]
        best_simple[name] = result["best_simple"]
    output = run_locked_evaluation(
        pools, records, dev, test, tuned, best_simple, budget=.5,
        budget_sweep=(.25, .5), random_reps=3, bootstrap_resamples=100,
    )
    assert set(output["results"]["same_pipeline"]["LR (tuned)"].shape) == {4}
    assert len(output["main_results"]) == 24
    assert len(output["comparisons"]) == 7
    assert len(output["mechanism_test"]) == 3
    assert len(output["budget_sweep"]) == 2