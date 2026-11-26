import numpy as np

from memweave.data import build_text_vectorizer
from memweave.transfer import build_locomo_conversations, cluster_bootstrap


def test_locomo_parser_preserves_session_order_and_evidence_indices():
    raw = [{
        "conversation": {
            "speaker_a": "Alice",
            "session_1": [
                {"speaker": "Alice", "text": "I visited Paris yesterday."},
                {"speaker": "Bob", "text": "That sounds wonderful."},
            ],
            "session_2": [
                {"speaker": "Bob", "text": "We discussed cooking."},
                {"speaker": "Alice", "text": "I enjoy making pasta."},
            ],
        },
        "qa": [
            {"category": 1, "evidence": ["D1:0"]},
            {"category": 5, "evidence": ["D2:0"]},
            {"category": 2, "evidence": ["D2:1"]},
        ],
    }]
    texts = [
        "user: I visited Paris yesterday.\\nassistant: That sounds wonderful.",
        "assistant: We discussed cooking.\\nuser: I enjoy making pasta.",
    ]
    hashing, transformer = build_text_vectorizer()
    transformer.fit(hashing.transform(texts))
    conversations = build_locomo_conversations(raw, hashing, transformer)
    assert len(conversations) == 1
    assert conversations[0]["session_numbers"] == [1, 2]
    assert conversations[0]["qs"] == [{0}, {1}]
    assert conversations[0]["F"].shape == (2, 10)


def test_conversation_cluster_bootstrap_is_paired_and_deterministic():
    treatment = np.array([.7, .8, .6, .9])
    control = np.array([.4, .5, .5, .6])
    a = cluster_bootstrap(treatment, control, resamples=500, seed=4)
    b = cluster_bootstrap(treatment, control, resamples=500, seed=4)
    assert a == b
    assert a[0] == .25
    assert a[1] > 0