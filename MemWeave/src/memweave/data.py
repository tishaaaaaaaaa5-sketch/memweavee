"""LongMemEval-S ingestion and label-free text representation.

This module extracts the notebook's input preparation. It intentionally keeps
network acquisition separate: callers supply a local JSON path or parsed rows.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer

FP_RE = re.compile(r"\\b(?:i|i'm|i've|i'd|i'll|my|me|mine|myself)\\b", re.I)
DAY_RE = re.compile(r"\\s*(\\d{4})/(\\d{2})/(\\d{2})(?:\\s*\\(\\w+\\))?\\s*(?:(\\d{2}):(\\d{2}))?")


def parse_day(value: str) -> float:
    """Parse the notebook's YYYY/MM/DD [HH:MM] dates to fractional ordinals."""
    match = DAY_RE.match(value)
    if not match:
        raise ValueError(f"unsupported date format: {value!r}")
    year, month, day = (int(match[i]) for i in (1, 2, 3))
    hour, minute = int(match[4] or 0), int(match[5] or 0)
    return datetime.date(year, month, day).toordinal() + (hour * 60 + minute) / 1440.0


def session_stats(turns: list[tuple[str, str]], user_name: str = "user"):
    """Return rendered text and label-free session statistics."""
    full = "\\n".join(f"{role}: {text}" for role, text in turns)
    words = sum(len(text.split()) for _, text in turns)
    user_text = " ".join(text for role, text in turns if role == user_name)
    user_words = len(user_text.split())
    first_person = len(FP_RE.findall(user_text)) / max(user_words, 1)
    digit_rate = sum(char.isdigit() for char in user_text) / max(len(user_text), 1)
    return full, words, user_words, len(turns), first_person, digit_rate


def find_file(name: str, roots=None) -> str | None:
    """Search explicit data roots and common notebook environments."""
    roots = roots or [
        os.environ.get("MEMWEAVE_DATA", ""), ".", "./data", "/kaggle/input",
        "/kaggle/working", "/content", "/mnt/user-data/uploads",
    ]
    for root in roots:
        if root and Path(root).exists():
            matches = sorted(Path(root).rglob(name))
            if matches:
                return str(matches[0])
    return None


def load_json(path: str | Path, *, max_questions: int | None = None) -> list[dict[str, Any]]:
    """Load LongMemEval JSON without silently downloading benchmark data."""
    with Path(path).open(encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError("LongMemEval JSON must contain a list of questions")
    return rows[:max_questions] if max_questions else rows


def build_longmemeval_records(raw: list[dict[str, Any]]) -> tuple[dict, list[dict]]:
    """Reproduce notebook deduplication, gold labels, and question metadata."""
    unique = dict(text=[], words=[], user=[], turns=[], fp=[], digit=[])
    hash_to_index: dict[str, int] = {}
    questions = []
    for question in raw:
        gold_ids = set(question["answer_session_ids"])
        question_day = parse_day(question["question_date"])
        rows, hashes = [], set()
        sessions = question["haystack_sessions"]
        denominator = max(len(sessions) - 1, 1)
        for position, (session_id, date, session) in enumerate(zip(
            question["haystack_session_ids"], question["haystack_dates"], sessions
        )):
            turns = [(turn["role"], turn["content"]) for turn in session]
            digest = hashlib.md5(
                "\\n".join(f"{role}:{text}" for role, text in turns).encode()
            ).hexdigest()
            if digest not in hash_to_index:
                index = len(unique["text"])
                full, words, user_words, count, fp, digit = session_stats(turns)
                hash_to_index[digest] = index
                unique["text"].append(full)
                unique["words"].append(words)
                unique["user"].append(user_words)
                unique["turns"].append(count)
                unique["fp"].append(fp)
                unique["digit"].append(digit)
            index = hash_to_index[digest]
            is_gold = session_id in gold_ids
            kind = "gold" if is_gold else (
                "filler" if session_id.startswith(("sharegpt", "ultrachat")) else "generated"
            )
            rows.append({
                "h": index, "sid": session_id, "gold": is_gold, "kind": kind,
                "day": parse_day(date), "pos": position / denominator,
            })
            hashes.add(index)
        questions.append({
            "qid": question["question_id"], "qtype": question["question_type"],
            "is_abs": question["question_id"].endswith("_abs"),
            "qday": question_day, "rows": rows, "all_hashes": hashes,
            "question": question["question"], "answer": str(question["answer"]),
        })
    for key in ("words", "user", "turns", "fp", "digit"):
        unique[key] = np.asarray(unique[key], dtype=np.float64)
    return unique, questions


def build_text_vectorizer():
    """Return the exact hashing + sublinear TF-IDF configuration from the notebook."""
    hashing = HashingVectorizer(
        n_features=2**19, alternate_sign=False, norm=None, lowercase=True,
        stop_words="english",
        token_pattern=r"(?u)\\b[a-zA-Z][a-zA-Z0-9']+\\b",
        dtype=np.float32,
    )
    return hashing, TfidfTransformer(sublinear_tf=True)


def fit_text_representation(texts: list[str], *, batch_size: int = 400):
    """Fit notebook-compatible TF-IDF and return (hashing vectorizer, transformer, X)."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    hashing, transformer = build_text_vectorizer()
    batches = [hashing.transform(texts[i:i + batch_size])
               for i in range(0, len(texts), batch_size)]
    if not batches:
        raise ValueError("at least one session text is required")
    matrix = transformer.fit_transform(sparse.vstack(batches).tocsr())
    return hashing, transformer, matrix.astype(np.float32).tocsr()


def prepare_longmemeval(raw: list[dict[str, Any]], *, batch_size: int = 400):
    """Build deduplicated sessions, question records, and TF-IDF matrices."""
    unique, questions = build_longmemeval_records(raw)
    hashing, transformer, matrix = fit_text_representation(unique["text"], batch_size=batch_size)
    question_matrix = transformer.transform(
        hashing.transform([question["question"] for question in questions])
    ).astype(np.float32).tocsr()
    return {
        "sessions": unique, "questions": questions, "hashing_vectorizer": hashing,
        "tfidf_transformer": transformer, "X": matrix, "X_questions": question_matrix,
    }
