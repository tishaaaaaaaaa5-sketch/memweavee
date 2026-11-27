# Evaluation Gap Closure

**Status:** Scoring infrastructure added; no benchmark improvement is claimed.

## Gap-to-work mapping

| Limitation | Infrastructure in this branch | Still needed for an empirical claim |
|---|---|---|
| Gold evidence recall | Held-out evidence scorer for gold, retained, and retrieved evidence IDs | Human-labelled held-out questions, adjudication, conversation-cluster split |
| Answer accuracy | Frozen-reader output scorer for normalized exact match, token F1, and abstention | Generate outputs for every selector using the same immutable reader setup |
| Exact tokenizer cost | Tokenizer-injected counter with tokenizer ID, exact-text hash, token count, bytes | Pin the production tokenizer and exact storage/chat serialization, including metadata/template overhead |
| LR / MW-ECS distinction | Explicitly separate the browser heuristic from learned and proposed methods | Train LR on train/dev only; implement and evaluate MW-ECS independently |

## Data contract

Each record passed to `memweave.heldout_eval.evaluate_records` contains:

- `question_id`: unique question identifier;
- `gold_evidence_ids`: manually adjudicated minimum sufficient evidence IDs;
- `retained_evidence_ids`: evidence preserved in persistent memory;
- `retrieved_evidence_ids`: evidence actually passed to the reader;
- `answerable`: whether the reference evidence supports an answer;
- `gold_answer`, `predicted_answer`, and `abstained`.

The scorer keeps retention recall, retrieval recall, and answer metrics separate. It rejects duplicate question IDs, duplicate evidence IDs, missing fields, and empty gold evidence sets. It scores abstention on answerable and unanswerable questions separately.

## Frozen-reader requirements

Record the immutable reader identifier/version, prompt SHA-256, decoding-configuration SHA-256, and tokenizer ID. Keep these identical across selector arms. A reader or prompt change starts a new experiment. This module scores outputs; it does not invoke a model.

## Exact-cost requirements

The token counter measures only the exact string passed to the caller-supplied encoder. To make a real budget claim:
1. Pin tokenizer name and revision.
2. Serialize exactly what is stored, including metadata and delimiters.
3. Hash the serialized text and record token count and UTF-8 bytes.
4. Separately count the actual reader input after applying the chat template.
5. Report storage tokens and inference-input tokens separately, and test budget violations per example.

A browser word-count proxy is not an exact model-token cost.

## Selector validity gates

The browser Coverage + MMR heuristic remains a demonstration baseline. It is not the trained logistic-regression selector and is not MW-ECS.

For LR, record training data, features, scaler, class balance, regularisation, calibration, development-only threshold selection, seed, and frozen artifact. Fit transforms and thresholds on train/development only.

For MW-ECS, specify the implemented objective, candidate unit, exact cost, solver, hyperparameters, and ablations. Do not claim an approximation guarantee without a proof for the implemented objective.

## Required experiment sequence

1. Run a two-annotator pilot using a minimum-sufficient-evidence rubric; adjudicate disagreements.
2. Lock a split by source conversation/cluster, not by individual question.
3. Compare random, recency, existing heuristic, LR, and MW-ECS at matched exact-token budgets.
4. Pass every selected memory to the same frozen reader.
5. Record storage tokens, reader-input tokens, latency, and model calls.
6. Report paired conversation-cluster bootstrap intervals and predeclare the primary budget/metric.
7. Preserve dataset revision/checksum, split IDs, code commit, configurations, model/tokenizer versions, seeds, output hashes, and failed runs.

## Claims permitted after this code change

- Reusable scoring utilities exist for manually labelled evidence and frozen-reader outputs.
- A tokenizer-injected counter exists for a caller-supplied serialization and tokenizer.

## Claims not established

No gold evidence recall gain, answer-accuracy gain, end-to-end exact-token compliance, trained LR result, or validated MW-ECS result is established by this infrastructure alone. Those require held-out data and completed experiments.
