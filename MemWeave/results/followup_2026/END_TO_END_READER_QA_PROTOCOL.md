# End-to-end reader QA evaluation protocol

**Status:** implemented in Notebook 05; awaiting Kaggle execution.  
**Purpose:** test whether memory selection improves actual generated answer quality, rather than only retaining benchmark evidence.

## Research question

At a matched, exact tokenizer-counted storage budget, does the frozen MemWeave role-aware selector produce better answers than the frozen baseline selector when both feed the same fixed reader?

## Dataset and provenance

- Dataset: LoCoMo, using the pinned revision and SHA-256 already recorded by Notebook 05.
- LoCoMo contains ten conversation clusters. It has previously been used for selector-transfer analysis, so this is a new answer-quality endpoint on previously examined benchmark material, not untouched independent confirmation.
- The LongMemEval-trained baseline and role-aware selectors are frozen; no LoCoMo fitting, calibration, or tuning is allowed.

## Predeclared protocol

- Reader: google/flan-t5-small, with the exact Hugging Face model revision resolved and recorded at run time.
- Sample: deterministic sample of up to 20 answerable, evidence-annotated questions per conversation (up to 200 questions).
- Primary comparison: role_aware versus baseline.
- Controls: recency and question_only.
- Storage budget: 10% of the full conversation's memory text, measured with the reader's tokenizer. Selection is greedy by frozen selector score subject to this exact token budget.
- Retrieval: top 3 sessions from each selected memory using the existing frozen TF-IDF representation and query similarity.
- Reader prompt: identical instruction and question format across methods; maximum 512 input tokens; greedy decoding; maximum 64 generated tokens.
- Primary metrics: exact match and token-level F1.
- Inference: paired bootstrap over conversation clusters, not individual questions. Ten clusters mean uncertainty will remain substantial.

## Required outputs

Notebook writes privacy-safe outputs under memweave_followup_outputs/locomo_reader_qa/:

- locomo_reader_qa_per_question.csv
- locomo_reader_qa_summary.csv
- locomo_reader_qa_paired_cluster_bootstrap.json
- locomo_reader_qa_manifest.json

No raw questions, reference answers, prompts, conversation text, or generated answer text are exported.

## Interpretation rules

1. Evidence recall remains distinct from answer quality.
2. The primary result is role-aware minus baseline token F1, with its conversation-cluster bootstrap interval.
3. A positive point estimate with an interval crossing zero is inconclusive, not a win.
4. If the question-only control matches or exceeds contextual methods, the reader may be relying on parametric knowledge or question priors.
5. A single small reader model does not establish model-independent benefit.
6. This experiment does not validate MFAR's failure diagnosis or intervention controller; it evaluates the preceding MemWeave selector-to-answer pathway only.
