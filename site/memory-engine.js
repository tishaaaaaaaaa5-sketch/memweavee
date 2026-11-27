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
    if (/\b(research priorities|priorities are|top priorities|priority is)\b/.test(t)) return "priorities";
    if (/\b(main goal|primary goal|research objective|objective is|goal is|purpose of|aims? to|studies how|designed to preserve)\b/.test(t)) return "goal";
    if (/\b(milestone|deliverable|next step|deadline)\b/.test(t)) return "milestone";
    if (/\b(evaluation metrics?|measuring|accuracy|evidence coverage|answerability|retrieval accuracy|token f1|recall|token.cost)\b/.test(t)) return "metrics";
    if (/\b(pytorch|tensorflow|python|cuda|gpu|scikit.learn|programming language|technical stack|fixed random seeds)\b/.test(t)) return "technical";
    if (/\b(should prioritize|durable preferences|technical constraints|important decisions|selection principle|must not|do not|never)\b/.test(t)) return "principles";
    return "general";
  }
  function queryIntent(text) { return evidenceType(text); }

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

  function buildCandidates(messages) {
    const out = [];
    messages.forEach((message, messageIndex) => {
      splitSentences(message.text).forEach((text, sentenceIndex) => {
        const words = countWords(text);
        if (!words) return;
        out.push({
          id: message.id + "-u" + (sentenceIndex + 1),
          sourceId: message.id,
          source: message.source,
          role: message.role,
          messageIndex,
          sentenceIndex,
          position: out.length,
          text,
          sourceText: message.text,
          words,
          kind: evidenceType(text)
        });
      });
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
      const recency = candidates.length > 1 ? index / (candidates.length - 1) : 0.5;
      const firstPerson = Math.min(1, firstPersonHits / Math.max(1, candidate.words / 12));
      const novelty = 1 - maxSimilarity;
      const compactness = Math.max(0, 1 - Math.abs(candidate.words - 24) / 48);
      const durable = /\b(must|should|always|never|do not|please keep|rather than|not be described|require|constraint)\b/i.test(candidate.text) ? 1 : 0;
      const researchSignal = candidate.kind !== "general" ? 1 : /\b(research|experiment|benchmark|dataset|model|method|baseline|retention|retrieval|evidence|memory)\b/i.test(candidate.text) ? 0.55 : 0;
      // Fixed transparent demo heuristic; deliberately not the trained LR model.
      const score = 0.24 * userRole + 0.13 * recency + 0.17 * novelty +
        0.07 * firstPerson + 0.07 * Math.min(1, digitRate * 12) +
        0.08 * compactness + 0.14 * durable + 0.10 * researchSignal;
      const reasons = [];
      if (userRole > 0.5) reasons.push("user-authored");
      if (candidate.kind !== "general") reasons.push(candidate.kind + " evidence");
      if (durable) reasons.push("durable instruction / constraint");
      if (novelty > 0.72) reasons.push("low redundancy in candidate pool");
      if (recency > 0.7) reasons.push("recent turn");
      if (firstPerson > 0.25) reasons.push("first-person signal");
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

  function selectCandidates(candidates, wordBudget, options = {}) {
    const mode = options.mode || "rank";
    const lambda = Number.isFinite(+options.lambda) ? Math.max(0, +options.lambda) : 0.25;
    if (!["rank", "density", "mmr"].includes(mode)) throw new Error("Unknown selection mode: " + mode);
    const budget = Math.max(0, Math.floor(Number(wordBudget) || 0));
    const chosen = [], trace = [], skipped = [];
    const available = new Set(candidates.map((_, i) => i));
    let used = 0;
    while (available.size) {
      let best = -1, bestUtility = -Infinity, bestPenalty = 0;
      for (const index of [...available].sort((a, b) => a - b)) {
        const item = candidates[index];
        if (used + item.words > budget) continue;
        let redundancy = 0;
        if (mode === "mmr") for (const prior of chosen) {
          redundancy = Math.max(redundancy, candidates[prior].similarities?.[index] ??
            cosine(tfidfVectors([item.text, candidates[prior].text])[0], tfidfVectors([item.text, candidates[prior].text])[1]));
        }
        const base = mode === "density" ? item.score / Math.max(1, item.words) : item.score;
        const utility = mode === "mmr" ? base - lambda * redundancy : base;
        if (utility > bestUtility + 1e-12) {
          best = index; bestUtility = utility; bestPenalty = redundancy;
        }
      }
      if (best < 0) break;
      chosen.push(best); available.delete(best); used += candidates[best].words;
      trace.push({
        id: candidates[best].id, order: chosen.length, score: candidates[best].score,
        utility: bestUtility, words: candidates[best].words,
        redundancy: bestPenalty, cumulativeWords: used
      });
    }
    const selectedSet = new Set(chosen);
    candidates.forEach((candidate, index) => {
      if (!selectedSet.has(index)) skipped.push({
        id: candidate.id, words: candidate.words, score: candidate.score,
        reason: used + candidate.words > budget
          ? "Does not fit in the remaining word-proxy budget as a complete evidence unit."
          : "Not selected by the marginal utility order."
      });
    });
    return {
      selected: chosen.map(index => candidates[index]),
      selectedIndices: chosen,
      trace, skipped, usedWords: used, wordBudget: budget,
      remainingWords: Math.max(0, budget - used), mode, lambda
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
    evidenceType, queryIntent
  };
});
