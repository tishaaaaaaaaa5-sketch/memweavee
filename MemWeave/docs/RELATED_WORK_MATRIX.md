# MemWeave related-work matrix — initial scan

**Review status:** Initial scoped scan, not a systematic review.  
**Last checked:** 2026-11-26.  
**Evidence standard:** The entries below are based on publisher/ACL Anthology pages or paper abstracts inspected during the initial scan. Unless explicitly stated otherwise, full methods, appendices, code, and experimental protocols still require verification. Do not cite an abstract-only reading as a full-paper review.

## Why this matrix exists

MemWeave Strategy C must distinguish three related but different problems:

1. **Memory admission/retention:** what to keep under a storage budget before the future query is known.
2. **Query-time retrieval/utilisation:** how to retrieve and combine evidence after a query arrives.
3. **Evaluation:** whether a system retains, updates, forgets, and correctly uses evidence.

A paper may address more than one category. The categories below are an initial reading aid, not a definitive taxonomy.

## Matrix

| Work | Year / venue | Main focus (from inspected source) | Relation to MemWeave | Verification status / next action |
|---|---|---|---|---|
| MemGPT: Towards LLMs as Operating Systems | 2023 preprint | Tiered/virtual context management for long interactions. | Foundational memory-management architecture; not a direct fixed-budget session selector comparison without adapting its task. | Project/paper abstract inspected; verify full paper and implementation. |
| MemoryBank: Enhancing LLMs with Long-Term Memory | AAAI 2024 | Long-term conversational memory with memory updating/forgetting inspired by a forgetting curve. | Relevant to temporal decay and memory update baselines. | AAAI publisher abstract inspected; verify method and reproducible setup. |
| Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo) | ACL 2024 | Benchmark of long conversations and QA, summarisation, and multimodal dialogue tasks. | External conversation-level evaluation; small number of conversation clusters requires cluster-aware inference. | ACL Anthology page inspected; verify dataset splits, annotation and licences. |
| LongMemEval | 2024 preprint / benchmark | 500 questions over long histories; extraction, multi-session, temporal, update, and abstention abilities. | Existing primary benchmark in MemWeave; audit task definitions and evidence-label construction. | Paper abstract and benchmark description inspected; verify full protocol and dataset revision. |
| Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory | 2025 / ECAI 2025 proceedings | Dynamic extraction, consolidation and retrieval; graph extension. | Strong practical memory-system comparator; not necessarily the same query-agnostic fixed-budget task. | Paper abstract and proceedings page inspected; verify exact configurations and licence. |
| A-Mem: Agentic Memory for LLM Agents | NeurIPS 2025 | Dynamically organised, interconnected memories with evolving links/attributes. | Closest structured-memory comparator; test whether graph/link organisation changes retention under a matched budget. | NeurIPS proceedings abstract inspected; verify full paper, code and comparable settings. |
| Know Me, Respond to Me (PersonaMem) | 2025 preprint | Dynamic user profiling and personalised response benchmark. | Tests evolving user preferences; useful for state updates and user-personalisation generalisation. | Abstract inspected; verify benchmark access, data terms and task compatibility. |
| Adaptive Memory Admission Control for LLM Agents (A-MAC) | ICLR 2026 MemAgents | Interpretable multi-factor memory admission using utility, confidence, novelty, recency and content type. | Directly overlaps multi-factor admission; must be treated as a close competitor to the proposed MW-ECS feature family. | OpenReview/paper abstract inspected; verify full method, code and budget matching. |
| MemRefine: LLM-Guided Compression for Long-Term Agent Memory | 2026 preprint | Budgeted memory-store maintenance via LLM-guided delete/merge/preserve decisions. | Direct budgeted-memory competitor; compare storage maintenance objective and LLM cost. | arXiv abstract inspected; verify full paper, benchmark and implementation. |
| UTILMEM: Benchmarking Evidence Utilization in Long-Term Conversational Memory | 2026 preprint | Evaluates evidence integration, implicit relevance, synthesis and distractor resistance beyond pointwise recall. | Important motivation for a downstream utilisation track and hard-distractor tests. | arXiv abstract inspected; verify full benchmark construction and evaluator. |
| From Recall to Forgetting (Memora) | Findings of ACL 2026 | Long-term remembering, reasoning, recommending, and forgetting-aware accuracy for obsolete/updated memories. | Close evaluation-framework comparator for updates, deletion and stale-memory penalties. | ACL Anthology entry and abstract inspected; verify full paper, data/code and scoring details. |
| Chain-of-Memory (CoM) | ACL 2026 | Lightweight memory construction and dynamic organisation of retrieved fragments into inference paths. | Relevant to the retention-to-reasoning gap and utilisation stage; compare cost and downstream QA. | ACL Anthology entry and abstract inspected; verify full method and exact compute comparisons. |
| Lightweight LLM Agent Memory with Small Language Models (LightMem) | ACL 2026 | SLM-driven writing, retrieval, and consolidation with short/mid/long-term memory. | Relevant efficiency and lifecycle comparator; evaluate if feasible under fixed budgets. | ACL Anthology abstract inspected; verify full method and model/runtime details. |
| MemORAI | Findings of ACL 2026 | Selective filtering, compression, provenance-enriched relational graph, query-adaptive retrieval. | Close competitor on provenance and memory filtering; separate its query-aware retrieval from query-agnostic retention. | ACL Anthology abstract inspected; verify full method and code. |
| Long-Term Agent Memory through Complementary Curation and Consolidation | Findings of AACL 2026 | Combines episodic and structured relational memories with consolidation. | Directly motivates complementarity; MW-ECS must show what its set-coverage term adds beyond hybrid representations. | ACL Anthology abstract inspected; verify full paper and benchmark protocol. |
| ProgMem: Programmatic Belief-State Memory for Long-Horizon Conversational Agents | Findings of AACL 2026 | Structured belief-state memory, temporal updates and evidence checking. | Relevant comparator for temporal state, supersession and evidence-grounded QA. | ACL Anthology abstract inspected; verify full method, code and evaluation details. |

## Preliminary implications for MemWeave

1. **Multi-factor memory admission is not itself a novelty claim.** A-MAC already describes an interpretable admission decision with several utility-related factors. MemWeave needs a more precise contribution than adding another weighted feature list.
2. **Budgeted memory maintenance is already directly studied.** MemRefine is an important close competitor, although its LLM-guided merge/delete/preserve process may differ from query-agnostic selection over original sessions.
3. **Complementarity and structured memory are active directions.** The AACL 2026 complementary-curation work and ProgMem mean that a generic claim about cross-session complementarity or temporal state would be too broad.
4. **Evidence recall is insufficient as the only evaluation.** UTILMEM and CoM explicitly address the gap between retrieving evidence and using it to reason or answer. MemWeave should keep retention and downstream QA as separate tracks.
5. **Forgetting and updates deserve explicit tests.** Memora's FAMA framing suggests a measurable failure mode that the current Stage B/C retention metric does not capture.
6. **Query-aware and query-agnostic tasks must remain separate.** Systems such as MemORAI and retrieval-oriented methods can exploit the current question; that is not a fair primary-track comparison with future-query-blind retention.

## Novelty statement — deliberately unresolved

At this stage, no defensible novelty statement has been established. A candidate direction worth investigating is:

> A query-agnostic, exact-budget session selector that optimises coverage of complementary, provenance-traceable evidence and is evaluated jointly on retained-evidence quality, downstream answer utility, update/forgetting robustness, and compute cost.

This is only a candidate synthesis. The closest-work full-text review must determine whether the combination is genuinely new, whether a narrower contribution is required, or whether MemWeave's strongest contribution should instead be the evaluation protocol.

## Full-text verification checklist

For each closest competitor (at minimum A-MAC, MemRefine, Memora, UTILMEM, CoM, MemORAI, ProgMem, A-Mem, Mem0, and the complementary-curation paper), record:

- [ ] Full paper and appendix read.
- [ ] Exact task definition and information available at memory-write/selection time.
- [ ] Memory unit (message, session, fact, summary, graph node, or belief state).
- [ ] Budget definition and tokenizer/counting method.
- [ ] Training/evaluation split and whether conversations overlap.
- [ ] Baselines, reader model, prompt and decoding settings.
- [ ] Primary metrics and uncertainty/statistical unit.
- [ ] Code availability, licence, and ability to reproduce.
- [ ] Exact overlap and difference from MemWeave recorded in a comparison note.

## Sources

- MemGPT: https://arxiv.org/abs/2310.08560
- MemoryBank: https://doi.org/10.1609/AAAI.V38I17.29946
- LoCoMo: https://aclanthology.org/2024.acl-long.747/
- LongMemEval: https://arxiv.org/abs/2410.10813
- Mem0: https://arxiv.org/abs/2504.19413
- A-Mem: https://papers.nips.cc/paper_files/paper/2025/hash/19909c36f51abc4856b4560aff3d36d6-Abstract-Conference.html
- PersonaMem: https://arxiv.org/abs/2504.14225
- A-MAC: https://openreview.net/pdf/3a8ba70bb8efe017018cebc9cf4bec9763d8bf77.pdf
- MemRefine: https://arxiv.org/abs/2606.13177
- UTILMEM: https://arxiv.org/abs/2608.30508
- Memora: https://aclanthology.org/2026.findings-acl.1337/
- Chain-of-Memory: https://aclanthology.org/2026.acl-long.534/
- LightMem: https://aclanthology.org/2026.acl-long.588/
- MemORAI: https://aclanthology.org/2026.findings-acl.1408/
- Complementary Curation and Consolidation: https://aclanthology.org/2026.findings-aacl.218/
- ProgMem: https://aclanthology.org/2026.findings-aacl.120/
