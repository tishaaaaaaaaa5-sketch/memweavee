import numpy as np
import pytest

from memweave.data import (
    build_longmemeval_records, fit_text_representation, parse_day, session_stats,
)


def tiny_questions():
    return [{
        "answer_session_ids": ["gold-1"],
        "question_date": "2024/01/03 (Wed) 12:00",
        "haystack_session_ids": ["gold-1", "sharegpt-2", "gen-3"],
        "haystack_dates": ["2024/01/01", "2024/01/02", "2024/01/02"],
        "haystack_sessions": [
            [{"role": "user", "content": "I remember 42 apples"},
             {"role": "assistant", "content": "You mentioned apples"}],
            [{"role": "user", "content": "A conversation about music"}],
            [{"role": "user", "content": "A conversation about travel"}],
        ],
        "question_id": "q1", "question_type": "multi-session",
        "question": "How many apples?", "answer": "42",
    }]


def test_date_and_session_statistics():
    assert parse_day("2024/01/03 (Wed) 12:00") == pytest.approx(
        parse_day("2024/01/03") + .5
    )
    full, words, user_words, turns, fp, digit = session_stats(
        [("user", "I have 42 apples"), ("assistant", "Okay")]
    )
    assert full.startswith("user: I have 42 apples")
    assert (words, user_words, turns) == (6, 4, 2)
    assert fp == pytest.approx(.25)
    assert digit == pytest.approx(2 / len("I have 42 apples"))


def test_record_builder_deduplicates_content_and_keeps_gold_labels():
    sessions, questions = build_longmemeval_records(tiny_questions())
    assert len(sessions["text"]) == 3
    q = questions[0]
    assert q["qid"] == "q1" and q["qtype"] == "multi-session"
    assert [row["kind"] for row in q["rows"]] == ["gold", "filler", "generated"]
    assert [row["gold"] for row in q["rows"]] == [True, False, False]
    assert len(q["all_hashes"]) == 3


def test_record_builder_deduplicates_identical_text_across_questions():
    raw = tiny_questions()
    second = dict(raw[0], question_id="q2")
    sessions, questions = build_longmemeval_records(raw + [second])
    assert len(sessions["text"]) == 3
    assert questions[0]["all_hashes"] == questions[1]["all_hashes"]


def test_hashing_tfidf_is_l2_normalized_and_deterministic():
    texts = ["apples and pears", "travel by train", "apples are tasty"]
    hv1, tf1, x1 = fit_text_representation(texts, batch_size=2)
    hv2, tf2, x2 = fit_text_representation(texts, batch_size=3)
    assert x1.shape == (3, 2**19)
    assert np.allclose(np.asarray(x1.multiply(x1).sum(1)).ravel(), 1.0)
    assert np.allclose((x1 - x2).toarray(), 0.0)
    assert hv1.n_features == hv2.n_features
