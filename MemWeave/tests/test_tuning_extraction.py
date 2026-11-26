import numpy as np

from memweave.features import FEATURES
from memweave.modeling import make_folds
from memweave.tuning import tune_pool


def test_dev_tuning_returns_frozen_configuration_without_test_data():
    pool = {"same_pipeline": {}}
    records = []
    rng = np.random.default_rng(4)
    for q in range(4):
        features = rng.normal(size=(3, len(FEATURES)))
        features[0, 0] += 2
        pool["same_pipeline"][q] = {
            "F": features,
            "gold": np.array([True, False, False]),
            "h": np.arange(q * 3, q * 3 + 3),
            "cost": np.ones(3),
            "S": np.eye(3),
        }
        records.append({"all_hashes": set(range(q * 3, q * 3 + 3))})
    dev = [0, 1, 2, 3]
    folds = make_folds(dev, folds=2, seed=2026)
    result = tune_pool(
        pool, records, "same_pipeline", dev, folds,
        C_grid=[.3], groups={"all": FEATURES},
        selection_options=[("rank", 0.0)], budget=.5,
    )
    assert result["config"]["C"] == .3
    assert result["config"]["groups"] == ["all"]
    assert result["config"]["idx"] == list(range(len(FEATURES)))
    assert result["config"]["mode"] == "rank"
    assert result["best_simple"] in {
        "recency", "longest", "high_centrality", "low_novelty"
    }
    assert len(result["tune_rows"]) == 6
