import numpy as np

from memweave.runner import _stable_ids_sha256


def test_split_fingerprint_is_stable_for_python_and_numpy_integer_ids():
    assert _stable_ids_sha256([1, 2, 3]) == _stable_ids_sha256(
        [np.int64(1), np.int64(2), np.int64(3)]
    )


def test_split_fingerprint_preserves_order():
    assert _stable_ids_sha256([1, 2, 3]) != _stable_ids_sha256([3, 2, 1])
