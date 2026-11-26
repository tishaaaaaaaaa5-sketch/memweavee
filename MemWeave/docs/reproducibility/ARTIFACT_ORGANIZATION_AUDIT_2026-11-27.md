# MemWeave artifact intake and organization audit

**Audit date:** 2026-11-27  
**Branch reviewed:** `research/memweave-followup-release`  
**Upload commit inspected:** `a8d27a625d7d11d56883225ccf99fa7df866fbfa` (`Add files via upload`)

## 1. What was added

The upload commit adds two files at the repository root, outside the `MemWeave/` project directory:

- `MemWeave_Research_Artifacts.zip` — 1,582,636 bytes.
- `notebookfef7168ab3 (3).ipynb` — 509,171 bytes.

The notebook is a consolidated executed Kaggle workbench, not a clean replacement for canonical Notebook 06. It has 88 cells, 78 executed code cells, and outputs in 74 cells. It contains the Stage B/C reconciliation workflow plus later MFAR trace assembly/audit work, LoCoMo reader-QA, Long-MT-Bench+ span-budget evaluation, and role-feature ablation/debug cells.

The final notebook cell reports that the ZIP was created from 52 files, was 1.51 MiB, passed `ZipFile.testzip()`, and had SHA-256:

`32bc3f886f569a8fe788ca62b37032fe51d44178184b432539a7b224b7575634`

The ZIP itself is binary and its internal file list/checksums could not be enumerated through the repository text interface. However, inspection of the notebook's actual export cell confirms the archive is built recursively from **all files under** `/kaggle/working/memweave_followup_outputs`, plus matching corrected ablation CSVs elsewhere under `/kaggle/working`, and includes `SHA256_MANIFEST.json`. Kaggle reports 52 files, successful `ZipFile.testzip()`, and the SHA-256 recorded above. Thus the outputs are bundled; the remaining limitation is that I have not independently extracted the uploaded binary to enumerate its exact contents and compare every manifest hash.

**Branch placement:** the upload commit is not present in the reviewed `research/memweave-followup-release` tree. The two uploaded files therefore are not yet part of the research branch's organized project tree.

## 2. Correct placement

Do not replace canonical notebooks with the consolidated execution snapshot.

| Current upload | Recommended location | Treatment |
|---|---|---|
| `notebookfef7168ab3 (3).ipynb` | `MemWeave/notebooks/archive/06_MemWeave_Consolidated_Kaggle_Execution_2026-11-26.ipynb` | Preserve as an execution archive; do not present as the canonical source notebook |
| `MemWeave_Research_Artifacts.zip` | `MemWeave/results/artifacts/2026-11-26/MemWeave_Research_Artifacts.zip` | Keep as a release bundle only after inspecting its contents, excluding prohibited raw benchmark text, and verifying every manifest hash |

Keep the existing canonical sequence intact:
- Notebooks 00–05: original pipeline, final role-aware run, and follow-up reader-QA workflow.
- Notebook 06: controlled Stage B/C reconciliation.
- The uploaded 88-cell notebook: archived consolidated execution record only.

The uploaded notebook contains historical diagnostics and failed/intermediate cells. In particular:
- Its earlier role-feature ablation cells 83–84 are superseded by cell 85.
- Cell 85 is the corrected LongMemEval leave-one-role-feature-out result using the actual six role columns (10–15); its summary is descriptive, not a causal feature-importance result.
- Cell 79's Long-MT-Bench+ individual role-feature ablation errored and is not a completed result.
- Cell 86 is a zero-score return-shape diagnostic, not an experiment and not a reason to discard cell 85.

## 3. Existing repository structure is broadly sound

The project already has appropriate homes for its content:
- `docs/`: algorithm, instrumentation, provenance, and reproducibility specifications.
- `notebooks/`: canonical source notebooks and an archive for executed snapshots.
- `results/`: result narratives, reconciliations, and dated experiment reports.
- `results/tables/`: compact, privacy-reviewed aggregate CSV tables.
- `schemas/`: machine-readable trace contracts and examples.
- `scripts/` and `tests/`: validators, trace assembly/audit utilities, and tests.

The new MFAR documents, scripts, schema, and 2026-11-26 retention-audit report are in sensible locations. The dated report correctly limits its claim to retention-stage audit results and leaves all four MFAR failure modes unobserved.

## 4. Confirmed status and remaining gaps

### Completed or documented
- Stage B/C controlled reconciliation and its eight-export manifest.
- Candidate-level export checksum recorded in the audited companion manifest.
- 49,140 candidate rows, 2,115 question-condition traces, 235 TEST questions, and nine conditions are reported.
- Retention trace assembly, schema validation, unit tests, and cross-stage referential-integrity validation are reported as passed.
- Retention audit report records 2,115 traces and explicitly leaves construction, compression, retrieval, and answering as `NOT_OBSERVABLE`.
- LoCoMo span-packing results for FLAN-T5-small and FLAN-T5-base, and corrected Long-MT-Bench+ span-budget results, are documented elsewhere in `results/`.
- Corrected LongMemEval individual role-feature ablation is present in the uploaded notebook's saved output.

### Still missing before a reproducible public release
1. **Artifact inventory:** extract the uploaded ZIP and publish its exact file list, sizes, and SHA-256 values. Compare the extracted files with the notebook's 52-file manifest and the recorded ZIP SHA-256.
2. **Research-branch integration:** move/copy the notebook into the archive location above and put the ZIP in the dated results artifact location only after the privacy review. The upload commit currently leaves both at repository root and outside the research branch.
3. **Bundle-to-repository integration:** the export notebook packages the contents of `memweave_followup_outputs` and the corrected ablation CSV(s) into the 52-file ZIP. Those individual exports are not all committed as standalone files in the research-branch tree, but they may be present in the uploaded bundle. The next check is to enumerate the ZIP and reconcile its manifest against the expected Stage B/C, MFAR, and QA artifact inventory; do not describe these exports as absent from the bundle.
4. **Corrected ablation detail:** publish the corrected aggregate ablation CSV. The notebook's corrected cell saves summary metrics only; it does not preserve per-question ablation scores or paired uncertainty intervals. Do not publish the earlier malformed/obsolete ablation outputs as valid results.
5. **MFAR real-runtime run:** execute Notebook 01 with `MFAR_TRACE_ENABLED=1` on the approved original data, then provide the real event JSONL and coverage/checksum manifest. Validate event lineage and compare traced versus untraced outputs. The committed hooks are instrumentation code, not runtime evidence.
6. **MFAR stage coverage:** current Stage B/C adapter evidence covers retention only. Separate retrieval, compression, and answer events remain unobserved unless the real pipeline emits them; no failure detector, labels, or MFAR effectiveness claim is yet supported.
7. **Privacy and data governance:** inspect the ZIP for raw conversation/session text, prompts, answers, private identifiers, and linkable hashes before release. Dataset terms and access controls must be recorded.
8. **Independent confirmation:** LongMemEval/LoCoMo/Long-MT-Bench+ results remain exploratory at their stated cluster counts. A larger, independently sampled conversational benchmark is still needed.

## 5. Documentation cleanup

Some older README paragraphs still say that LoCoMo reader QA is pending, that a second reader has no results, or that the Stage B/C candidate trace is yet to be generated. These statements are superseded by the later dated result reports and audit manifest. The project index should point readers to the latest dated reports and clearly separate:
- retention/evidence recall;
- downstream answer QA;
- partial MFAR retention traces;
- real runtime instrumentation (pending execution).

Do not combine these into one headline metric or describe the retention audit as a validated MFAR controller.
