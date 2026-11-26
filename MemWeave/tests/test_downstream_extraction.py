import numpy as np
from scipy import sparse

from memweave.downstream import answer_eligible, downstream_question, evaluate_downstream_proxy


def test_downstream_proxy_retrieves_evidence_and_checks_answer_string():
    texts = ["The user lives in Paris.", "A discussion about cooking.", "A story about hiking."]
    question = {
        "answer": "Paris",
        "rows": [
            {"h": 0, "gold": True}, {"h": 1, "gold": False}, {"h": 2, "gold": False},
        ],
    }
    pool_item = {
        "h": np.array([0, 1, 2]), "gold": np.array([True, False, False]),
    }
    x = sparse.csr_matrix([[1., 0.], [0., 1.], [.5, .5]])
    q = sparse.csr_matrix([[1., 0.]])
    assert answer_eligible(question, texts)
    result = downstream_question(pool_item, np.array([0, 1]), q, x, texts, question, topk=1)
    assert result["evidence_hit"] == 1.0
    assert result["answer_in_context"] == 1.0


def test_downstream_evaluation_reports_paired_method_differences():
    texts = ["The answer is Paris.", "Other content.", "More content."]
    question = {
        "answer": "Paris",
        "rows": [{"h": 0, "gold": True}, {"h": 1, "gold": False}, {"h": 2, "gold": False}],
    }
    pool_item = {"h": np.array([0, 1, 2]), "gold": np.array([True, False, False])}
    pools = {"same_pipeline": {0: pool_item}}
    x = sparse.csr_matrix([[1., 0.], [0., 1.], [.5, .5]])
    q = sparse.csr_matrix([[1., 0.]])
    methods = {"LR (tuned)": {0: np.array([0, 1])}, "recency": {0: np.array([1, 2])}}
    result = evaluate_downstream_proxy(
        pools, {0: question}, x, {0: q}, texts, [0], methods,
        bootstrap_resamples=100,
    )
    assert result["summary"].loc[0, "evidence_hit@3"] == 1.0
    assert len(result["paired_comparisons"]) == 1
    assert result["paired_comparisons"].loc[0, "hit_diff"] == 0.0