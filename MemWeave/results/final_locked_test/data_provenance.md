# MemWeave data provenance and export inventory

## Benchmark source

The role-aware locked-test notebook loads **LongMemEval-S cleaned** from the public Hugging Face dataset repository:

- Dataset page: https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned
- Expected source file: `longmemeval_s_cleaned.json`
- The notebook's loader first searches local Kaggle/Colab paths and `MEMWEAVE_DATA`, then downloads the file from the dataset URL if absent.

The final locked-test output supplied with this repository snapshot does **not** include a SHA-256 for the exact LongMemEval-S file used by that run. Do not substitute the hash from an unrelated earlier run manifest. A future rerun should write the dataset SHA-256 into the run manifest before training/evaluation.

## What is committed

- `notebooks/04_MemWeave_Final_Executed.ipynb`: executed notebook source, 94 code cells with execution counts preserved. Debug outputs that exposed full conversation text were removed; the final locked-test and paired statistical audit outputs are retained.
- `results/paired_test_audit.json`: aggregate locked-test inference and provenance flags.
- `results/question_type_breakdown.csv`: aggregate subgroup results transcribed from the final saved audit output.

## What is not committed

The notebook reports that it wrote `memweave_role_aware_locked_test.csv`, `memweave_role_aware_question_type_audit.csv`, and `memweave_role_aware_audit_manifest.json` in the Kaggle working directory. Those files were **not present** in the uploaded notebook/output archive available for this repository update. The per-question CSV has therefore not been reconstructed or fabricated.

The benchmark contains conversational histories. Do not publish raw message content, answers, or session text as an evaluation export. The appropriate shareable raw export should contain only per-question identifiers, question type, baseline/role-aware ranks, budgeted recall values, and derived paired differences—without question text, answers, or conversation contents—and should include a dataset license/provenance note and checksums.

## Reproduction checklist

1. Obtain `longmemeval_s_cleaned.json` from the source dataset under its current terms.
2. Record its SHA-256 and dataset revision.
3. Set `MEMWEAVE_DATA` to the directory containing the file.
4. Run the executed notebook from a clean kernel using the frozen configuration.
5. Confirm the OOF reconstruction checks pass exactly before unlocking the TEST evaluation.
6. Save the three audit exports listed above and add their SHA-256 checksums to the manifest.
7. Keep question-level bootstrap inference distinct from conversation-cluster inference.