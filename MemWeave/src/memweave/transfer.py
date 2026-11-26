"""LoCoMo conversation parsing and external transfer evaluation."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from .data import session_stats
from .features import FEATURES, GROUPS, build_features
from .modeling import stack_questions
from .selection import select_indices


def build_locomo_conversations(data, hashing_vectorizer, tfidf_transformer):
    """Parse LoCoMo conversations and evidence indices using LongMemEval TF-IDF.

    Speaker A is mapped to user and speaker B to assistant, matching the notebook.
    Category-5 questions are excluded; conversations without evidence questions
    remain present because conversation is the cluster/bootstrap unit.
    """
    conversations = []
    for record in data:
        conversation = record["conversation"]
        speaker_a = conversation.get("speaker_a")
        numbers = sorted(
            int(key.split("_")[1]) for key in conversation
            if re.fullmatch(r"session_\d+", key)
        )
        texts, words, user_words, turns_count, first_person, digit_rate = [], [], [], [], [], []
        for number in numbers:
            turns = [
                ("user" if turn["speaker"] == speaker_a else "assistant", turn.get("text", ""))
                for turn in conversation[f"session_{number}"]
            ]
            full, word_count, user_count, count, fp, digit = session_stats(turns, "user")
            texts.append(full)
            words.append(word_count)
            user_words.append(user_count)
            turns_count.append(count)
            first_person.append(fp)
            digit_rate.append(digit)
        questions = []
        for qa in record.get("qa", []):
            if qa.get("category") == 5:
                continue
            evidence_numbers = {
                int(match) for evidence in qa.get("evidence", [])
                for match in re.findall(r"D(\d+):", str(evidence))
            }
            evidence_indices = {numbers.index(number) for number in evidence_numbers if number in numbers}
            if evidence_indices:
                questions.append(evidence_indices)
        if not numbers:
            continue
        vectors = tfidf_transformer.transform(
            hashing_vectorizer.transform(texts)
        ).astype(np.float32).tocsr()
        features, similarity = build_features(
            vectors, np.asarray(words, dtype=float), np.asarray(user_words, dtype=float),
            np.asarray(turns_count, dtype=float), np.asarray(first_person),
            np.asarray(digit_rate), np.arange(len(numbers), dtype=float), None,
        )
        conversations.append({
            "F": features, "S": similarity, "cost": np.asarray(words, dtype=float),
            "qs": questions, "n": len(numbers), "session_numbers": numbers,
        })
    return conversations


def cluster_bootstrap(treatment, control, *, resamples=4000, seed=3):
    """Paired bootstrap over conversations (not QA rows)."""
    treatment = np.asarray(treatment, dtype=float)
    control = np.asarray(control, dtype=float)
    if treatment.ndim != 1 or control.ndim != 1 or len(treatment) != len(control) or not len(treatment):
        raise ValueError("paired conversation scores must be non-empty equal-length vectors")
    if resamples < 1:
        raise ValueError("resamples must be positive")
    difference = treatment - control
    rng = np.random.default_rng(seed)
    sampled = difference[rng.integers(0, len(difference), (resamples, len(difference)))].mean(1)
    return (float(difference.mean()), float(np.percentile(sampled, 2.5)),
            float(np.percentile(sampled, 97.5)))


def evaluate_locomo_transfer(pools, question_records, training_question_ids,
                             conversations, tuned_config, *, pool="same_pipeline",
                             budget=0.10, random_reps=50, seed=0,
                             bootstrap_resamples=4000):
    """Train on all LongMemEval questions and evaluate per-conversation LoCoMo recall.

    No LoCoMo labels are used for fitting or configuration selection. The two
    model variants drop the date feature; role-free additionally drops style.
    """
    config = tuned_config
    transfer_indices = [i for i, name in enumerate(FEATURES) if name != "log_days_before"]
    base_indices = [i for i in config["idx"] if i in transfer_indices] or transfer_indices
    style_features = set(GROUPS["style"])
    role_free_indices = [i for i in base_indices if FEATURES[i] not in style_features]
    if not role_free_indices:
        role_free_indices = [i for i, name in enumerate(FEATURES)
                             if name not in style_features and name != "log_days_before"]
    x_train, y_train, _ = stack_questions(
        pools[pool], training_question_ids, base_indices
    )
    model_transfer = LogisticRegression(
        C=config["C"], class_weight="balanced", max_iter=500
    ).fit(x_train, y_train)
    x_role, y_role, _ = stack_questions(
        pools[pool], training_question_ids, role_free_indices
    )
    model_role_free = LogisticRegression(
        C=config["C"], class_weight="balanced", max_iter=500
    ).fit(x_role, y_role)

    def conversation_scores(score_function, mode="rank", penalty=0.0, repetitions=None):
        per_conversation = []
        for conversation in conversations:
            if repetitions:
                rng = np.random.default_rng(seed)
                chosen = [
                    select_indices(rng.random(conversation["n"]), conversation["cost"],
                                   conversation["S"], budget)
                    for _ in range(repetitions)
                ]
            else:
                chosen = [select_indices(
                    score_function(conversation), conversation["cost"],
                    conversation["S"], budget, mode=mode, redundancy_penalty=penalty,
                )]
            question_recalls = [
                np.mean([len(set(selection.tolist()) & evidence) / len(evidence)
                         for selection in chosen])
                for evidence in conversation["qs"]
            ]
            per_conversation.append(float(np.mean(question_recalls)) if question_recalls else np.nan)
        return np.asarray(per_conversation, dtype=float)

    scores = {"random": conversation_scores(None, repetitions=random_reps)}
    scores["recency"] = conversation_scores(lambda c: c["F"][:, 2])
    scores["low_novelty"] = conversation_scores(lambda c: -c["F"][:, 7])
    scores["high_centrality"] = conversation_scores(lambda c: c["F"][:, 8])
    scores["LR (transfer)"] = conversation_scores(
        lambda c: model_transfer.predict_proba(c["F"][:, base_indices])[:, 1],
        config["mode"], config["lam"],
    )
    scores["LR (role-free)"] = conversation_scores(
        lambda c: model_role_free.predict_proba(c["F"][:, role_free_indices])[:, 1],
        config["mode"], config["lam"],
    )
    rows = []
    for model_name in ("LR (transfer)", "LR (role-free)"):
        for baseline in ("recency", "low_novelty", "random"):
            mean, low, high = cluster_bootstrap(
                scores[model_name], scores[baseline],
                resamples=bootstrap_resamples, seed=seed + 3,
            )
            rows.append({
                "method": model_name, "vs": baseline,
                "method_recall": float(np.nanmean(scores[model_name])),
                "other_recall": float(np.nanmean(scores[baseline])),
                "diff": mean, "ci_low": low, "ci_high": high,
            })
    valid_transfer = scores["LR (transfer)"][np.isfinite(scores["LR (transfer)"])]
    valid_random = scores["random"][np.isfinite(scores["random"])]
    sd = float(np.std(valid_transfer - valid_random, ddof=1)) if len(valid_transfer) > 1 else 0.0
    count = len(valid_transfer)
    mde = (1.96 + 0.84) * sd / np.sqrt(count) if count else float("nan")
    return {
        "conversation_scores": scores, "comparisons": pd.DataFrame(rows),
        "n_conversations": len(conversations),
        "n_questions_with_evidence": sum(len(c["qs"]) for c in conversations),
        "minimum_detectable_difference": float(mde),
    }