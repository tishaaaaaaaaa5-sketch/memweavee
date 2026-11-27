/* MemWeave evidence engine: transparent browser baseline, not a trained research model. */
(function(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.MemWeaveEngine = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function() {
  "use strict";
  const STOPWORDS = new Set(("a an the and or but if then than is am are was were be been being do does did can could would should will may might must have has had having i me my mine we our you your he she it they them this that these those what which who whom when where why how to of in on at by for from with about as into over under after before between through during up down out not no yes please tell explain").split(/\s+/));

  function countWords(text) {
    return (String(text || "").match(/[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*/g) || []).length;
  }
  function tokens(text) {
    return (String(text || "").toLowerCase().match(/[a-z0-9]+/g) || [])
      .filter(t => t.length > 2 && !STOPWORDS.has(t));
  }
  function uniqueTokens(text) { return [...new Set(tokens(text))]; }
  function evidenceType(text) {
    const t = String(text || "").toLowerCase();
    if (/\b(research priorit(?:y|ies)|priorities are|top priorities|priority is)\b/.test(t)) return "priorities";
    if (/\b(memweave goal|main goal|primary goal|research objective|objective is|goal is|purpose of|aims? to|studies how|designed to preserve)\b/.test(t)) return "goal";
    if (/\b(milestone|deliverable|next step|deadline)\b/.test(t)) return "milestone";
    if (/\b(must not be described|never equate|separate evidence recall|tie claims to|benchmark reports|reporting rule|should not describe|do not describe|not be described|must be kept distinct)\b/.test(t)) return "principles";
    if (/\b(token.cost|word.count estimate|cost accounting|exact token|pytorch|tensorflow|python|cuda|gpu|scikit.learn|programming language|technical stack|fixed random seeds)\b/.test(t)) return "technical";
    if (/\b(evaluation metrics?|measuring|accuracy|evidence coverage|answerability|retrieval accuracy|token f1|recall)\b/.test(t)) return "metrics";
    if (/\b(should prioritize|durable preferences|technical constraints|important decisions|selection principle|must not|do not|never)\b/.test(t)) return "principles";
    return "general";
  }
  function queryIntent(text) { return evidenceType(text); }

  // Fine-grained selection facets are separate from coarse retrieval evidence types.
  function evidenceFacet(text) {
    const value = String(text || "").toLowerCase();
    const kind = evidenceType(value);
    if (kind === "priorities") {
      if (/evidence retention|retaining evidence|retain evidence/.test(value)) return "priority:evidence_retention";
      if (/downstream answer quality|answer quality/.test(value)) return "priority:downstream_answer_quality";
      if (/reproducib|reproducible|reproducibility/.test(value)) return "priority:reproducibility";
      return "priority:other";
    }
    if (kind === "technical") {
      if (/tokenizer|token.cost|word.count estimate|exact token/.test(value)) return "hard:token_accounting";
      if (/python|scikit.learn|pytorch|tensorflow|cuda|gpu/.test(value)) return "technical:stack";
    }
    if (kind === "principles" && /benchmark|evidence recall|answer accuracy/.test(value)) return "principles:benchmark_reporting";
    return kind;
  }

  function parseConversation(input, source = "Pasted conversation") {
    const raw = String(input || "").replace(/\r/g, "");
    const lines = raw.split("\n");
    const marker = /^\s*(user|assistant|system|human|ai|speaker\s*\w*)\s*:\s*(.*)$/i;
    if (!lines.some(line => marker.test(line))) {
      return raw.split(/\n\s*\n/).map(x => x.trim()).filter(Boolean).map((text, i) => ({
        id: "m" + (i + 1), role: "unlabelled", text, words: countWords(text),
        messageIndex: i, source
      }));
    }
    const messages = [];
    let current = null;
    function flush() {
      if (current && current.text.trim()) {
        current.text = current.text.trim();
        current.words = countWords(current.text);
        current.messageIndex = messages.length;
        current.source = source;
        current.id = "m" + (messages.length + 1);
        messages.push(current);
      }
      current = null;
    }
    for (const line of lines) {
      const match = line.match(marker);
      if (match) {
        flush();
        const rawRole = match[1].toLowerCase();
        current = {
          role: /^(user|human)$/.test(rawRole) ? "user" :
                /^(assistant|ai)$/.test(rawRole) ? "assistant" : rawRole,
          text: match[2] || ""
        };
      } else if (current) {
        current.text += (current.text ? "\n" : "") + line;
      } else if (line.trim()) {
        current = { role: "unlabelled", text: line.trim() };
      }
    }
    flush();
    return messages;
  }

  function splitSentences(text) {
    const value = String(text || "").trim();
    if (!value) return [];
    const pieces = [];
    let start = 0;
    for (let i = 0; i < value.length; i++) {
      const ch = value[i];
      if (ch !== "." && ch !== "?" && ch !== "!") continue;
      let next = i + 1;
      while (next < value.length && /\s/.test(value[next])) next++;
      if (next < value.length && !/[A-Z0-9"'“‘([]/.test(value[next])) continue;
      const part = value.slice(start, i + 1).trim();
      if (part) pieces.push(part);
      start = next;
      i = next - 1;
    }
    const tail = value.slice(start).trim();
    if (tail) pieces.push(tail);
    return pieces.length ? pieces : [value];
  }

  function atomicClaims(sentence) {
    const value = String(sentence || "").trim();
    const clean = value.replace(/[.!?]+$/, "").trim();
    if (!clean) return [];

    // Split only when the second clause repeats its subject. Do this before
    // specialised compression so a separate technical clause is never discarded.
    const repeatedSubject = clean.match(/^(.+?),\\s+and\\s+(I|we|they|he|she)\\s+(.+)$/i);
    if (repeatedSubject) return [
      ...atomicClaims(repeatedSubject[1]),
      ...atomicClaims(repeatedSubject[2] + " " + repeatedSubject[3])
    ];

    // Preserve the contrast while shortening the explicit tokenizer-cost requirement.
    if (/token.cost|tokenizer/i.test(clean) && /word.count|word count/i.test(clean)) return [{
      text: "Cost requirement: exact tokenizer tokens, not word-count estimates.",
      derivation: "context_resolved"
    }];

    const priority = clean.match(/^(?:my\\s+)?research priorities are\\s+(.+)$/i);
    if (priority) {
      const parts = priority[1].split(/,\\s*(?:and\\s+)?/i).map(x => x.trim()).filter(Boolean);
      if (parts.length > 1) return parts.map(part => ({
        text: "Research priority: " + part.replace(/^[a-z]/, c => c.toLowerCase()) + ".",
        derivation: "context_resolved"
      }));
    }

    const goal = clean.match(/^(?:my\\s+)?main goal is to build\\s+([^,]+),\\s+a research system that preserves\\s+(.+?)\\s+under a strict memory budget$/i);
    if (goal) return [{
      text: goal[1].trim() + " goal: preserve " + goal[2].trim() + " under a strict memory budget.",
      derivation: "context_resolved"
    }];

    return [{ text: value, derivation: "source_exact" }];
  }

  function buildCandidates(messages) {
    const out = [];
    messages.forEach((message, messageIndex) => {
      const sentences = splitSentences(message.text);
      for (let i = 0; i < sentences.length; i++) {
        const current = sentences[i];
        const next = sentences[i + 1] || "";
        // Two linked reporting instructions are retained as one compact rule, with the
        // full original message preserved as provenance for inspection.
        const benchmarkRule = /benchmark.{0,30}report|report.{0,30}benchmark/i.test(current) &&
          /evidence recall.{0,50}answer accuracy/i.test(next);
        const claims = benchmarkRule
          ? [{ text: "Tie claims to benchmark reports; separate evidence recall from answer accuracy.", derivation: "context_resolved" }]
          : atomicClaims(current);
        if (benchmarkRule) i++;

        claims.forEach((claim, claimIndex) => {
          const words = countWords(claim.text);
          if (!words) return;
          const sentenceIndex = out.filter(x => x.sourceId === message.id).length;
          out.push({
            id: message.id + "-u" + (sentenceIndex + 1),
            sourceId: message.id,
            source: message.source,
            role: message.role,
            messageIndex,
            sentenceIndex,
            unitIndex: claimIndex,
            position: out.length,
            text: claim.text,
            sourceText: message.text,
            words,
            kind: evidenceType(claim.text),
            facet: evidenceFacet(claim.text),
            derivation: claim.derivation
          });
        });
      }
    });
    return out;
  }

  function tfidfVectors(documents) {
    const docs = documents.map(tokens);
    const df = new Map();
    docs.forEach(doc => new Set(doc).forEach(term => df.set(term, (df.get(term) || 0) + 1)));
    const N = Math.max(1, docs.length);
    return docs.map(doc => {
      const counts = new Map();
      doc.forEach(term => counts.set(term, (counts.get(term) || 0) + 1));
      const vector = new Map();
      for (const [term, count] of counts) {
        const idf = Math.log(1 + (N + 1) / (1 + (df.get(term) || 0)));
        vector.set(term, (1 + Math.log(count)) * idf);
      }
      const norm = Math.sqrt([...vector.values()].reduce((sum, v) => sum + v * v, 0)) || 1;
      for (const [term, value] of vector) vector.set(term, value / norm);
      return vector;
    });
  }
  function cosine(a, b) {
    let sum = 0;
    const [small, large] = a.size <= b.size ? [a, b] : [b, a];
    for (const [term, value] of small) sum += value * (large.get(term) || 0);
    return Math.max(0, Math.min(1, sum));
  }
  function similarityMatrix(documents) {
    const vectors = tfidfVectors(documents);
    return vectors.map((vector, i) => vectors.map((other, j) => i === j ? 0 : cosine(vector, other)));
  }

  function scoreCandidates(candidates) {
    const sims = similarityMatrix(candidates.map(c => c.text));
    const messageIds = [...new Set(candidates.map(c => c.messageIndex))];
    const messageRank = new Map(messageIds.map((id, index) => [
      id, messageIds.length > 1 ? index / (messageIds.length - 1) : 0.5
    ]));
    const kindBonus = {
      goal: 0.10, priorities: 0.09, technical: 0.10,
      principles: 0.14, metrics: 0.06, milestone: 0.07, general: 0
    };
    return candidates.map((candidate, index) => {
      const row = sims[index] || [];
      const others = row.filter((_, j) => j !== index);
      const maxSimilarity = others.length ? Math.max(...others) : 0;
      const meanSimilarity = others.length ? others.reduce((a, b) => a + b, 0) / others.length : 0;
      const top3 = [...others].sort((a, b) => b - a).slice(0, 3);
      const firstPersonHits = (candidate.text.toLowerCase().match(/\b(i|me|my|mine|we|our|ours)\b/g) || []).length;
      const digits = (candidate.text.match(/\d/g) || []).length;
      const digitRate = digits / Math.max(1, candidate.text.length);
      const userRole = candidate.role === "user" ? 1 : candidate.role === "assistant" ? 0.15 : 0;
      const recency = messageRank.get(candidate.messageIndex) ?? 0.5;
      const firstPerson = Math.min(1, firstPersonHits / Math.max(1, candidate.words / 12));
      const novelty = 1 - maxSimilarity;
      const compactness = Math.max(0, 1 - Math.abs(candidate.words - 24) / 48);
      const durable = /\b(must|should|always|never|do not|please keep|rather than|not be described|require|constraint|exact)\b/i.test(candidate.text) ? 1 : 0;
      const researchSignal = candidate.kind !== "general" ? 1 :
        /\b(research|experiment|benchmark|dataset|model|method|baseline|retention|retrieval|evidence|memory)\b/i.test(candidate.text) ? 0.55 : 0;
      const isAssistantPrompt = candidate.role === "assistant" &&
        (/\?/.test(candidate.text) || /^\s*(what|which|who|where|when|why|how)\b/i.test(candidate.text));
      const bonus = (kindBonus[candidate.kind] || 0) +
        (/\b(exact token.cost|word.count estimate|scikit.learn)\b/i.test(candidate.text) ? 0.06 : 0) +
        (candidate.derivation === "context_resolved" ? 0.015 : 0);
      // Fixed transparent heuristic based on interpretable signals; not the trained LR model.
      const rawScore = 0.24 * userRole + 0.13 * recency + 0.17 * novelty +
        0.07 * firstPerson + 0.07 * Math.min(1, digitRate * 12) +
        0.08 * compactness + 0.14 * durable + 0.10 * researchSignal + bonus;
      const score = isAssistantPrompt ? 0.02 : Math.max(0.01, Math.min(1, rawScore));
      const reasons = [];
      if (isAssistantPrompt) reasons.push("assistant prompt; not user evidence");
      else {
        if (userRole > 0.5) reasons.push("user-authored evidence");
        if (candidate.kind !== "general") reasons.push((candidate.facet || candidate.kind) + " evidence facet");
        if (durable) reasons.push("durable instruction / constraint");
        if (novelty > 0.72) reasons.push("low redundancy in candidate pool");
        if (recency > 0.7) reasons.push("recent message");
        if (candidate.derivation === "context_resolved") reasons.push("context-resolved from source message");
      }
      if (!reasons.length) reasons.push("general conversation evidence");
      return {
        ...candidate, score, features: {
          logWords: Math.log1p(candidate.words),
          recencyRank: recency, userFraction: userRole,
          firstPersonRate: firstPerson, digitRate,
          novelty, meanSimilarity,
          top3Similarity: top3.length ? top3.reduce((a, b) => a + b, 0) / top3.length : 0
        },
        reasons, similarities: row
      };
    });
  }

  const FACET_WEIGHTS = Object.freeze({
    "hard:token_accounting": 2.0,
    "priority:evidence_retention": 1.35,
    "priority:downstream_answer_quality": 1.25,
    "priority:reproducibility": 1.2,
    "principles:benchmark_reporting": 1.15,
    "technical:stack": 0.85,
    "priority:other": 0.8
  });
  function facetWeight(facet) {
    return FACET_WEIGHTS[facet] || (facet && facet !== "general" ? 0.75 : 0);
  }
  function selectKnapsackCandidates(candidates, wordBudget, options = {}) {
    const budget = Math.max(0, Math.floor(Number(wordBudget) || 0));
    const maxOperations = 5000000;
    if (candidates.length * Math.max(1, budget) > maxOperations) {
      const fallback = selectCandidates(candidates, budget, { ...options, mode: "density" });
      return { ...fallback, mode: "knapsack", optimal: false,
        solver: "greedy-density fallback",
        solverNote: "Exact DP skipped because candidate-count × budget exceeded the 5,000,000-operation safety limit." };
    }
    const dp = new Array(budget + 1).fill(null);
    dp[0] = { value: 0, node: null };
    for (let i = 0; i < candidates.length; i++) {
      const cost = Math.max(1, Math.floor(Number(candidates[i].words) || 1));
      if (cost > budget) continue;
      for (let cap = budget; cap >= cost; cap--) {
        const previous = dp[cap - cost];
        if (!previous) continue;
        const value = previous.value + Number(candidates[i].score || 0);
        if (!dp[cap] || value > dp[cap].value + 1e-12) {
          dp[cap] = { value, node: { index: i, previous: previous.node } };
        }
      }
    }
    let best = dp[0];
    for (let cap = 1; cap <= budget; cap++) if (dp[cap] && dp[cap].value > best.value + 1e-12) best = dp[cap];
    const indices = [];
    for (let node = best.node; node; node = node.previous) indices.push(node.index);
    indices.sort((a, b) => a - b);
    const selectedSet = new Set(indices);
    const selected = indices.map(i => candidates[i]);
    const usedWords = selected.reduce((sum, item) => sum + Math.max(1, Math.floor(Number(item.words) || 1)), 0);
    const coveredFacets = [...new Set(selected.map(x => x.facet || x.kind || "general").filter(x => x !== "general"))];
    const allFacets = [...new Set(candidates.map(x => x.facet || x.kind || "general"))];
    const totalFacetWeight = allFacets.reduce((sum, facet) => sum + facetWeight(facet), 0);
    const coveredFacetWeight = coveredFacets.reduce((sum, facet) => sum + facetWeight(facet), 0);
    let cumulativeWords = 0;
    const trace = selected.map((item, order) => {
      cumulativeWords += item.words;
      return { id: item.id, order: order + 1, score: item.score, utility: item.score,
        marginalUtilityPerWord: item.score / Math.max(1, item.words), words: item.words,
        redundancy: 0, coverageGain: 0, facetWeight: facetWeight(item.facet || item.kind || "general"),
        facet: item.facet || item.kind || "general", cumulativeWords };
    });
    const skipped = candidates.flatMap((candidate, index) => selectedSet.has(index) ? [] : [{
      id: candidate.id, words: candidate.words, score: candidate.score,
      reason: "Not included in the maximum additive-score subset that fits the budget."
    }]);
    return { selected, selectedIndices: indices, trace, skipped, usedWords,
      wordBudget: budget, remainingWords: Math.max(0, budget - usedWords),
      mode: "knapsack", lambda: 0, coverageBonus: 0, coveredFacets,
      coveredFacetWeight, totalFacetWeight,
      weightedFacetCoverage: totalFacetWeight ? coveredFacetWeight / totalFacetWeight : 0,
      optimal: true, solver: "exact 0/1 dynamic programming", objectiveValue: best.value };
  }

  function selectCandidates(candidates, wordBudget, options = {}) {
    const mode = options.mode || "rank";
    const lambda = Number.isFinite(+options.lambda) ? Math.max(0, +options.lambda) : 0.25;
    const coverageBonus = Number.isFinite(+options.coverageBonus) ? Math.max(0, +options.coverageBonus) : 0.22;
    const validModes = ["rank", "density", "mmr", "coverage_only", "coverage", "knapsack"];
    if (!validModes.includes(mode)) throw new Error("unknown selection mode: " + mode);
    if (mode === "knapsack") return selectKnapsackCandidates(candidates, wordBudget, options);
    const usesCoverage = mode === "coverage_only" || mode === "coverage";
    const usesMmr = mode === "mmr" || mode === "coverage";
    const budget = Math.max(0, Math.floor(Number(wordBudget) || 0));
    const chosen = [], trace = [], skipped = [];
    const available = new Set(candidates.map((_, i) => i));
    const coveredFacets = new Set();
    let used = 0;
    while (available.size) {
      let best = -1, bestUtility = -Infinity, bestPriority = -Infinity, bestPenalty = 0, bestCoverageGain = 0, bestFacetWeight = 0;
      for (const index of [...available].sort((a, b) => a - b)) {
        const item = candidates[index];
        if (used + item.words > budget) continue;
        let redundancy = 0;
        if (usesMmr) for (const prior of chosen) {
          redundancy = Math.max(redundancy, candidates[prior].similarities?.[index] ??
            cosine(tfidfVectors([item.text, candidates[prior].text])[0], tfidfVectors([item.text, candidates[prior].text])[1]));
        }
        const facet = item.facet || item.kind || "general";
        const weight = facetWeight(facet);
        const facetGain = usesCoverage && facet !== "general" && !coveredFacets.has(facet) ? coverageBonus * weight : 0;
        const base = mode === "density" ? item.score / Math.max(1, item.words) : item.score;
        const utility = base + facetGain - (usesMmr ? lambda * redundancy : 0);
        // Coverage policies use marginal utility per word; this remains a deterministic greedy heuristic.
        const priority = usesCoverage ? utility / Math.max(1, item.words) : utility;
        if (priority > bestPriority + 1e-12) {
          best = index; bestUtility = utility; bestPriority = priority;
          bestPenalty = redundancy; bestCoverageGain = facetGain; bestFacetWeight = weight;
        }
      }
      if (best < 0) break;
      const chosenItem = candidates[best];
      chosen.push(best); available.delete(best); used += chosenItem.words;
      const facet = chosenItem.facet || chosenItem.kind || "general";
      if (facet !== "general") coveredFacets.add(facet);
      trace.push({
        id: chosenItem.id, order: chosen.length, score: chosenItem.score,
        utility: bestUtility, marginalUtilityPerWord: bestPriority,
        words: chosenItem.words, redundancy: bestPenalty,
        coverageGain: bestCoverageGain, facetWeight: bestFacetWeight,
        facet, cumulativeWords: used
      });
    }
    const selectedSet = new Set(chosen);
    candidates.forEach((candidate, index) => {
      if (selectedSet.has(index)) return;
      const remaining = Math.max(0, budget - used);
      const facet = candidate.facet || candidate.kind || "general";
      let reason;
      if (candidate.words > remaining) reason = "Remaining word-proxy budget is too small for this complete evidence unit.";
      else if (usesCoverage && facet !== "general" && coveredFacets.has(facet)) reason = "This evidence facet is already represented; other facets had higher weighted marginal utility.";
      else if (usesMmr && chosen.some(i => (candidates[i].similarities?.[index] || 0) > 0.45)) reason = "High semantic/lexical overlap with evidence already selected.";
      else reason = "Lower marginal utility under the selected policy.";
      skipped.push({ id: candidate.id, words: candidate.words, score: candidate.score, reason });
    });
    const allFacets = [...new Set(candidates.map(x => x.facet || x.kind || "general"))];
    const totalFacetWeight = allFacets.reduce((sum, facet) => sum + facetWeight(facet), 0);
    const coveredFacetWeight = [...coveredFacets].reduce((sum, facet) => sum + facetWeight(facet), 0);
    return {
      selected: chosen.map(index => candidates[index]), selectedIndices: chosen,
      trace, skipped, usedWords: used, wordBudget: budget,
      remainingWords: Math.max(0, budget - used), mode, lambda, coverageBonus,
      coveredFacets: [...coveredFacets], coveredFacetWeight, totalFacetWeight,
      weightedFacetCoverage: totalFacetWeight ? coveredFacetWeight / totalFacetWeight : 0
    };
  }

  function rankEvidence(query, items, options = {}) {
    const qTokens = uniqueTokens(query);
    if (!qTokens.length || !items.length) return [];
    const queryIntentType = queryIntent(query);
    const docTokens = items.map(item => tokens(item.text));
    const df = new Map();
    docTokens.forEach(doc => new Set(doc).forEach(term => df.set(term, (df.get(term) || 0) + 1)));
    const N = Math.max(1, items.length);
    const avgdl = docTokens.reduce((sum, doc) => sum + doc.length, 0) / N || 1;
    const k1 = 1.2, b = 0.75;
    const q = String(query).toLowerCase();
    const candidates = items.map((item, index) => {
      const counts = new Map();
      docTokens[index].forEach(term => counts.set(term, (counts.get(term) || 0) + 1));
      const matched = qTokens.filter(term => counts.has(term));
      if (!matched.length) return null;
      let bm25 = 0;
      for (const term of qTokens) {
        const tf = counts.get(term) || 0;
        if (!tf) continue;
        const dfi = df.get(term) || 0;
        const idf = Math.log(1 + (N - dfi + 0.5) / (dfi + 0.5));
        bm25 += idf * (tf * (k1 + 1)) /
          (tf + k1 * (1 - b + b * docTokens[index].length / avgdl));
      }
      const phraseBonus = q.length > 8 && String(item.text).toLowerCase().includes(q) ? 0.25 : 0;
      const kind = item.kind || evidenceType(item.text);
      const intentBonus = queryIntentType !== "general" && kind === queryIntentType ? 0.18 :
        queryIntentType !== "general" && kind !== "general" ? -0.08 : 0;
      return {
        ...item, matched, coverage: matched.length / qTokens.length,
        bm25, phraseBonus, intentBonus,
        rawScore: Math.max(0, bm25 + phraseBonus + intentBonus),
        kind, queryIntent: queryIntentType
      };
    }).filter(Boolean);
    if (!candidates.length) return [];
    const max = Math.max(...candidates.map(x => x.rawScore), 1e-9);
    const sims = similarityMatrix(candidates.map(x => x.text));
    const lambda = Number.isFinite(+options.lambda) ? Math.max(0, +options.lambda) : 0.18;
    const limit = Math.max(1, Math.floor(+options.limit || 12));
    const remaining = new Set(candidates.map((_, i) => i));
    const chosen = [];
    while (remaining.size && chosen.length < limit) {
      let best = -1, bestValue = -Infinity, bestRedundancy = 0;
      for (const index of [...remaining].sort((a, b) => a - b)) {
        let redundancy = 0;
        for (const prior of chosen) redundancy = Math.max(redundancy, sims[index][prior]);
        const value = candidates[index].rawScore / max - lambda * redundancy;
        if (value > bestValue + 1e-12) {
          best = index; bestValue = value; bestRedundancy = redundancy;
        }
      }
      if (best < 0) break;
      remaining.delete(best);
      chosen.push({
        ...candidates[best],
        score: Math.max(0, Math.min(1, candidates[best].rawScore / max)),
        diversityPenalty: bestRedundancy,
        mmrScore: bestValue
      });
    }
    return chosen;
  }

  return {
    countWords, tokens, parseConversation, splitSentences, buildCandidates,
    similarityMatrix, scoreCandidates, selectCandidates, rankEvidence,
    evidenceType, evidenceFacet, queryIntent
  };
});
