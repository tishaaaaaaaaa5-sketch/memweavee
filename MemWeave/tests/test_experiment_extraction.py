import numpy as np

from memweave.data import build_longmemeval_records
from memweave.experiment import build_question_pools, locked_split
from test_data_extraction import tiny_questions


def test_pool_builder_and_locked_split_use_only_valid_questions():
    raw = tiny_questions()
    raw2 = dict(raw[0], question_id="q2")
    sessions, questions = build_longmemeval_records(raw + [raw2])
    # Synthetic vectors stand in for the already-fitted notebook TF-IDF matrix.
    matrix = np.array([[1., 0.], [0., 1.], [.8, .2]])
    pools = build_question_pools(questions, sessions, matrix)
    assert all(set(pools[p]) == {0, 1} for p in ("same_pipeline", "all", "filler"))
    split = locked_split(pools, questions, test_fraction=.5, seed=7)
    assert set(split["dev"]).isdisjoint(split["test"])
    assert set(split["dev"]) | set(split["test"]) == {0, 1}
