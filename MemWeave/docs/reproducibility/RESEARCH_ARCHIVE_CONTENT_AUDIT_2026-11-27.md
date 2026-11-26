# Research archive integrity, privacy and licensing audit — 2026-11-27

**Artifact:** `MemWeave/results/artifacts/2026-11-26/MemWeave_Research_Artifacts.zip`  
**Repository:** `tishaaaaaaaaa5-sketch/memweavee` (public)  
**Decision:** archive integrity passes; privacy/licensing release gate remains **blocked** until raw benchmark text is removed or separately justified and third-party terms are documented.

## 1. Independent integrity verification

The original ZIP was retrieved from the committed repository using a GitHub Actions audit job and independently extracted for inspection before it was withdrawn from the current `main` tree.

| Check | Result |
|---|---|
| ZIP size | 1,582,636 bytes |
| ZIP SHA-256 | `32bc3f886f569a8fe788ca62b37032fe51d44178184b432539a7b224b7575634` |
| Previously recorded Kaggle SHA-256 | Exact match |
| ZIP entries | 53 total: 52 payload files plus `SHA256_MANIFEST.json` |
| Manifest | 52 entries; `file_count = 52` |
| Per-file SHA-256 | 52/52 match |
| Per-file byte sizes | 52/52 match |
| ZIP CRC | Pass; no corrupt member |
| Duplicate paths | None |
| Absolute or parent-traversal paths | None |
| Symlinks | None |
| Executable-mode files | None |
| Total uncompressed size | 19,854,080 bytes |

The earlier “52 files” count refers to manifest-listed payload files, not the ZIP's total member count. The extra member is the manifest itself.

## 2. Content inventory and privacy findings

The archive contains 52 result files plus the manifest. Most are aggregate/per-question CSVs and JSON run manifests. Several per-question exports use 20-character SHA-256 prefixes for question identifiers; these are pseudonymous/linkable identifiers, not proof of anonymization.

**Important finding — cleartext LoCoMo dialogue is included.**

`memweave_followup_outputs/locomo_reader_qa_evidence_span_flan_t5_base/evidence_span_selections.csv` contains a `selected_spans` column with serialized span objects. Those objects include `speaker`, `text`, and `rendered` fields.

- 800 rows in the file; 600 rows contain selected spans.
- 26,913 selected span objects.
- Approximately 810,293 characters of cleartext span text.
- The text is benchmark conversation content, not merely a hash or aggregate metric.

This contradicts the broad statement that the release bundle contains only privacy-safe derived records. It must not be described as a privacy-safe export. The repository's public visibility makes this a real redistribution decision, not just a local-storage concern.

Other files include generated `prediction` text fields (including per-question reader outputs). They do not include the original question/prompt text in the inspected columns, but remain text-bearing outputs and should be retained only if their source-data terms permit it.

A basic scan found no email-address patterns, common API-key patterns, AWS access-key patterns, or PEM private-key headers. This is a narrow automated scan, not a full privacy review; it does not establish that the benchmark dialogue contains no personal or sensitive information.

## 3. Dataset licensing and attribution

### LoCoMo

The upstream `snap-research/locomo` repository publishes its dataset under **CC BY-NC 4.0**. The license permits sharing for non-commercial purposes subject to attribution and other conditions. The ZIP includes cleartext LoCoMo-derived dialogue spans, but the archive itself does not include a LoCoMo attribution/license notice or a modification notice.

Before continued public distribution of those spans, add the required dataset attribution, a link to the source and license, and a clear statement that the selected spans are derived/modified excerpts. Confirm that the intended distribution is non-commercial. If those conditions are not appropriate, remove the cleartext spans from the public release and regenerate the ZIP and manifest.

Sources:
- Dataset and license: https://github.com/snap-research/locomo
- License text: https://github.com/snap-research/locomo/blob/main/LICENSE.txt
- License URI: https://creativecommons.org/licenses/by-nc/4.0/

### Long-MT-Bench+

The archive includes per-question reader predictions and selection/audit metadata for Long-MT-Bench+. The Hugging Face dataset card describes the dataset fields (sessions, questions, turns and answers) but the inspected README/metadata does not state a license. The archive does not include the original conversation histories or questions in the inspected Long-MT-Bench+ result tables, but the permission status for redistributing derived per-question outputs should be resolved before release.

Source:
- Dataset card: https://huggingface.co/datasets/panzs19/Long-MT-Bench-Plus

## 4. Release decision and required actions

- [x] Independently recompute archive SHA-256.
- [x] Extract archive and test ZIP CRCs.
- [x] Reconcile all 52 manifest hashes and sizes.
- [x] Check paths, duplicate members, symlinks and executable bits.
- [x] Identify cleartext dialogue-bearing exports.
- [x] Withdraw the unsanitized archive from the current `main` tree.
- [ ] Resolve Long-MT-Bench+ redistribution terms for generated per-question outputs.
- [ ] Build a sanitized replacement excluding `evidence_span_selections.csv` and other unapproved text-bearing outputs; regenerate `SHA256_MANIFEST.json`.
- [ ] Re-run this audit against the final release candidate.
- [ ] Update README/data guidance so it accurately discloses the archive's text-bearing contents.

**Do not redistribute the historical archive or describe it as privacy-cleared.** The current tree no longer publishes it, but prior public commits still contain the ZIP. A sanitized replacement and separate history-removal decision remain outstanding. Integrity verification is not privacy or licensing clearance.
