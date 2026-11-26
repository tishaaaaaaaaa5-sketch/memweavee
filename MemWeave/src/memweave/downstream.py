"""Retrieval-based downstream proxy for retained conversational memory."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .inference import paired_bootstrap


def answer_eligible(question, session_texts, *, max_answer_chars=40):
    """Whether a short answer string literally occurs in at least one gold session."""
    answer = str(question.get("answer", "")).lower().strip()
    if not answer or len(answer) > max_answer_chars:
        return False
    return any(
        answer in session_texts[row["h"]].lower()
        for row in question["rows"] if row["gold"]
    )


def _selected_repetitions(value):
    """Normalise one selection or repeated random selections to a list of arrays."""
    if isinstance(value, (list, tuple)) and value and np.asarray(value[0]).ndim > 0:
        return [np.asarray(item, dtype=int) for item in value]
    return [np.asarray(value, dtype=int)]


def downstream_question(pool_item, selected, question_vector, session_matrix,
                        session_texts, question, *, topk=3, eligible=None):
    """Compute per-question evidence hit@k and answer-in-context@k.

    For repeated random selections, average the proxy over repetitions exactly as
    in the notebook. Answer-in-context is NaN for ineligible questions.
    """
    if topk < 1:
        raise ValueError("topk must be positive")
    indices = np.asarray(pool_item["h"], dtype=int)
    similarities = session_matrix[indices] @ question_vector.T\n    if hasattr(similarities, "toarray"):\n        similarities = similarities.toarray()\n    similarities = np.asarray(similarities).ravel()
    repeats = _selected_repetitions(selected)
    answer = str(question.get("answer", "")).lower().strip()
    is_eligible = answer_eligible(question, session_texts) if eligible is None else eligible
    hit_values, answer_values = [], []
    for chosen in repeats:
        top = chosen[np.argsort(-similarities[chosen], kind="stable")[:topk]] if len(chosen) else chosen
        hit_values.append(float(pool_item["gold"][top].any()) if len(top) else 0.0)
        if is_eligible:
            answer_values.append(float(any(
                answer in session_texts[indices[position]].lower() for position in top
            )) if len(top) else 0.0)
    return {
        "evidence_hit": float(np.mean(hit_values)),
        "answer_in_context": float(np.mean(answer_values)) if answer_values else np.nan,
        "answer_eligible": bool(is_eligible),
    }


def evaluate_downstream_proxy(pools, questions, session_matrix, question_matrix,
                              session_texts, question_ids, method_selections,
                              *, pool="same_pipeline", topk=3,
                              primary_method="LR (tuned)", comparisons=None,
                              bootstrap_resamples=4000, bootstrap_seed=7):
    """Evaluate method selection maps against question-conditioned retrieval.

    method_selections maps method names to {question_id: selected indices};
    a full-history ceiling can be supplied as all candidate indices. This
    proxy is not end-to-end LLM answer accuracy.
    """
    per_method = {}
    rows = []
    eligible_mask = np.asarray([
        answer_eligible(questions[q], session_texts) for q in question_ids
    ], dtype=bool)
    for method, selection_map in method_selections.items():
        hit, answer = [], []
        for q in question_ids:
            value = downstream_question(
                pools[pool][q], selection_map[q], question_matrix[q],
                session_matrix, session_texts, questions[q], topk=topk,
                eligible=bool(answer_eligible(questions[q], session_texts)),
            )
            hit.append(value["evidence_hit"])
            answer.append(value["answer_in_context"])
        hit, answer = np.asarray(hit), np.asarray(answer)
        per_method[method] = {"evidence_hit": hit, "answer_in_context": answer}
        rows.append({
            "pool": pool, "method": method, f"evidence_hit@{topk}": float(hit.mean()),
            f"answer_in_context@{topk}": float(np.nanmean(answer)) if eligible_mask.any() else np.nan,
            "n_questions": len(question_ids), "n_answer_eligible": int(eligible_mask.sum()),
        })
    summary = pd.DataFrame(rows)
    pairs = []
    if comparisons is None:
        comparisons = [name for name in method_selections if name != primary_method]
    if primary_method in per_method:
        for other in comparisons:
            if other not in per_method:
                raise ValueError(f"unknown comparison method: {other}")
            hit = paired_bootstrap(
                per_method[primary_method]["evidence_hit"],
                per_method[other]["evidence_hit"],
                resamples=bootstrap_resamples, seed=bootstrap_seed,
            )
            valid = eligible_mask
            if valid.any():
                answer = paired_bootstrap(
                    per_method[primary_method]["answer_in_context"][valid],
                    per_method[other]["answer_in_context"][valid],
                    resamples=bootstrap_resamples, seed=bootstrap_seed + 1,
                )
            else:
                answer = {"diff": np.nan, "ci_low": np.nan, "ci_high": np.nan, "p": np.nan}
            pairs.append({
                "pool": pool, "comparison": f"{primary_method} minus {other}",
                "hit_diff": hit["diff"], "hit_ci_low": hit["ci_low"],
                "hit_ci_high": hit["ci_high"], "answer_diff": answer["diff"],
                "answer_ci_low": answer["ci_low"], "answer_ci_high": answer["ci_high"],
            })
    return {"summary": summary, "paired_comparisons": pd.DataFrame(pairs),
            "per_method": per_method, "eligible": eligible_mask}