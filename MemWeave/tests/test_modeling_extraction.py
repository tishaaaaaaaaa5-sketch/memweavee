import numpy as np

from memweave.modeling import (
    cv_recall, fit_scores, make_folds, out_of_fold_scores,
)


def synthetic():
    pools = {"same_pipeline": {}}
    records = []
    for q in range(4):
        features = np.array([
            [1.0 + q * .01, 0.0],
            [0.0, 1.0 + q * .01],
            [.2, .8],
        ])
        pools["same_pipeline"][q] = {
            "F": features,
            "gold": np.array([True, False, False]),
            "h": np.array([q * 3, q * 3 + 1, q * 3 + 2]),
            "cost": np.array([1., 1., 1.]),
            "S": np.eye(3),
        }
        records.append({"all_hashes": set(range(q * 3, q * 3 + 3))})
    return pools, records


def test_model_fitting_excludes_held_out_session_hashes():
    pools, records = synthetic()
    scores, kept, total = fit_scores(
        pools, records, "same_pipeline", [0, 1, 2], [3], .3, [0, 1]
    )
    assert list(scores) == [3]
    assert scores[3].shape == (3,)
    assert kept == total == 9


def test_oof_scores_cover_each_dev_question_once():
    pools, records = synthetic()
    folds = make_folds([0, 1, 2, 3], folds=2, seed=11)
    scores = out_of_fold_scores(
        pools, records, "same_pipeline", folds, .3, [0, 1]
    )
    assert set(scores) == {0, 1, 2, 3}
    assert all(value.shape == (3,) for value in scores.values())


def test_cv_recall_is_bounded_and_deterministic():
    pools, records = synthetic()
    folds = make_folds([0, 1, 2, 3], folds=2, seed=11)
    a = cv_recall(pools, records, "same_pipeline", [0, 1, 2, 3],
                  folds, .3, [0, 1], budget=.5)
    b = cv_recall(pools, records, "same_pipeline", [0, 1, 2, 3],
                  folds, .3, [0, 1], budget=.5)
    assert 0 <= a <= 1
    assert a == b
