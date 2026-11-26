import numpy as np

from memweave.features import FEATURES
from memweave.robustness import evaluate_split_robustness


def test_split_seed_robustness_repeats_dev_tuning_without_global_state():
    rng = np.random.default_rng(12)
    pools = {"same_pipeline": {}}
    records = []
    for q in range(12):
        features = rng.normal(size=(4, len(FEATURES)))
        features[0, 0] += 1.0
        item = {
            "F": features, "gold": np.array([True, False, False, False]),
            "h": np.arange(q * 4, q * 4 + 4), "cost": np.ones(4), "S": np.eye(4),
        }
        pools["same_pipeline"][q] = item
        records.append({"all_hashes": set(range(q * 4, q * 4 + 4)), "qtype": str(q % 2)})
    result = evaluate_split_robustness(
        pools, records, list(range(12)), seeds=[11, 12], folds=2,
        C_grid=[.3], selection_options=[("rank", 0.0)],
        budget=.5, bootstrap_resamples=100,
    )
    assert result["split_seed"].tolist() == [11, 12]
    assert result["n_dev"].tolist() == [6, 6]
    assert result["n_test"].tolist() == [6, 6]
    assert np.all(result["ci_low"] <= result["ci_high"])