# Roadmap Priorities — Evidence-Driven Re-ordering

*Drafted 2026-10-20. Supersedes the "Recommended implementation order" in
[NEXT_FEATURES.md](NEXT_FEATURES.md); feature numbers below refer to that file.*

This document re-prioritises the roadmap around one question that keeps coming up:
**"Context windows are huge now — why do we still need retrieval?"**
The order below is chosen so that every step both improves the system *and*
produces measurable evidence for that conversation.

---

## 1. Why retrieval still matters here (the short version)

| Argument | Evidence | What it means for this project |
|---|---|---|
| The corpus does not fit | Indexed corpus: **6,396 chunks ≈ 1.8M tokens** (only selected sections; raw filings are 719 MB) | >14× GPT-4o-mini's 128k window, and beyond any 1M window. Some selection step is mandatory. |
| Long context degrades | Chroma "Context Rot" (18 models): accuracy falls as input grows, even on trivial tasks; a single distractor hurts. LongMemEval: every model scored higher on a ~300-token focused prompt than on the ~113k full prompt. | Filings are distractor-heavy by nature: the same metric appears across years, quarters and companies. |
| Long context wins accuracy only when it fits, at high cost | Hamilton et al. (Jun 2026): long context 73.1% vs semantic RAG 65.4%, at **26× the per-query token cost**. | Worth testing on single-filing questions (one 10-K ≈ 100–300k tokens). Not an option for cross-company / multi-year questions. |
| Dense-only retrieval is weak on financial text | arXiv 2604.01733 (23,088 queries, 7,318 text+table docs): **BM25 beat state-of-the-art dense retrieval**; best = hybrid + two-stage reranking (Recall@5 0.816); HyDE / multi-query added little on numeric queries; contextual retrieval gave consistent gains. | **Our current retriever is dense-only** (FAISS + metadata filters). This is our main exposure and the first thing to fix. |
| Cost per query | Current: ~$0.0005/query. Full corpus in context on GPT-4o-mini would be roughly $0.27/query (~500×), and several dollars on a frontier model *(estimates; check current pricing)*. | Retrieval is what makes the product economically viable. |

**Positioning:** the 2026 consensus is not "RAG *or* long context" but
**retrieve the right documents/sections, then let a long-context model reason over
them**, increasingly with the model calling retrieval as a tool (agentic retrieval).
The roadmap below moves the system in that direction.

---

## 2. Prioritised next steps

### P0 — Retrieval-level evaluation + long-context baseline *(new, ~1–1.5 days)*

**Why first:** today's eval measures *generation* (15 assertion cases + RAGAS
faithfulness/relevancy, which `evaluate.py` itself notes varies 0.33–0.94 between runs on
multi-company questions). Nothing measures *whether the right chunk was retrieved*,
so we cannot prove that hybrid search or reranking helps — or answer the CTO with data.

**Scope**
1. Golden set of **60–100 questions**, each labelled with expected source(s)
   (company, form, period_end, section — or chunk IDs) and, for figure questions,
   the exact expected number. Balanced across categories:
   - figure (single company / period)
   - narrative ("why did X move")
   - cross-company comparison
   - multi-year trend
   - temporal ("latest", "last quarter", fiscal-calendar edge cases)
   - out-of-corpus (must refuse)
2. New metrics in `eval/`: **Recall@k, MRR, nDCG** (retrieval), **Number Match**
   (exact numeric answer), citation correctness, refusal accuracy, cost and latency.
3. A **long-context arm**: for questions answerable from a single filing, send the
   whole filing (or its indexed sections) to a long-context model with no retrieval.
4. `--compare` reports results per category, not just a global mean.

**Done when:** one command produces a table of
*long-context vs current RAG vs each new improvement*, per category.

---

### P1 — Hybrid retrieval: BM25 + dense + rerank *(Feature 4 + new BM25 path, ~1 day)*

**Why:** strongest, most directly evidenced quality gain for financial text, and it
closes the "dense-only" gap.

1. **BM25 index** over the same chunks (`bm25s` or `rank_bm25`; tokenise preserving
   tickers, tags like `us-gaap:Revenues`, fiscal labels like `FY2024`, and numbers).
2. **Fusion** with FAISS via Reciprocal Rank Fusion (RRF); keep existing metadata
   filters and per-company diversity applied *after* fusion.
3. **Cross-encoder rerank (Feature 4):** fused top 30–50 → top 5–8. Benchmark
   `ms-marco-MiniLM-L-6-v2` against a stronger reranker (e.g. a `bge-reranker` model) —
   the MS MARCO model is general-domain.
4. **Contextual chunk headers** (if not already present): prepend
   `company · form · fiscal period · section` to each chunk's text before embedding *and*
   BM25 indexing. Cheap (metadata already exists), consistent gains in the benchmark.
   Requires re-running from `embed`.

**Measure with P0:** Recall@5 / MRR per category, before and after each sub-step.

---

### P2 — Query understanding *(Feature 9a + 9b + 9f; skip Feature 8, ~4–6h)*

**Why:** fixes the two documented failure modes — *"latest is semantic, not temporal"*
and fiscal-calendar mismatches (NVDA Jan / AAPL Sep / MSFT Jun year-ends).

- 9a: one cheap LLM call extracting companies, periods, source_type, intent → filters.
- 9b: query rewriting (same call). Note: the benchmark found HyDE / multi-query weak on
  numeric queries — rewrite toward **exact terms** (ticker, metric, FY) that help BM25,
  not toward hypothetical answers.
- 9f: deterministic date resolution ("latest" → max `period_end` per company).
- As already noted in NEXT_FEATURES, 9a subsumes Feature 8.

---

### P3 — Structured data as a tool *(Feature 1, go straight to step 4; + Feature 6, ~1.5 days)*

**Why:** this is *agentic retrieval* — the modern answer to "just use a big context".
The model asks for exact numbers when it needs them instead of relying on embeddings
of formatted numbers.

- Skip the keyword-trigger version (Feature 1 steps 1–3 as routing); implement
  `xbrl_raw.json` + a `get_financials(company, periods, metrics)` tool via tool-calling.
- Feature 6 (pre-computed annual comparisons) as a cheap complement for trend questions.
- Unlocks Feature 2 (charts) afterwards.

---

### P4 — "Retrieve, then read" with a larger context *(new, ~0.5–1 day, experimental)*

**Why:** combines both worlds. Once retrieval identifies the right filing/section,
pass the **whole section** (e.g. full MD&A for that period) instead of 5 chunks.

- Option in `qa.py`: expand top-ranked chunks to their parent section, capped by a
  token budget (e.g. 30–100k).
- Keep only if P0 shows gains on narrative/"why" questions that justify the cost.

---

### Later (unchanged priority, roughly in order)
- Feature 3 — config file for sections (1h quick win; can be done anytime).
- Feature 9c + 9d — session context + simplified UI.
- Feature 5 — feedback loop (feeds new golden-set questions into P0).
- Feature 7 — segment-level XBRL extension tags.
- Feature 2 — charts (after P3).

---

## 3. Summary table

| Priority | Item | Effort (manual) | Effort with Claude Code | Main metric to watch | Depends on |
|---|---|---|---|---|---|
| P0 | Retrieval eval + long-context baseline | 1–1.5d | **5–6h** (3–4h is human review of the golden set) | Recall@k, MRR, Number Match, cost | — |
| P1 | BM25 + RRF + rerank + contextual headers | ~1d | **3–4h** | Recall@5 / MRR on figure questions | P0 |
| P2 | Query understanding (9a/9b/9f) | 4–6h | **2–3h** | Temporal & fiscal-calendar categories | P0 |
| P3 | XBRL tool-calling + annual summaries (1, 6) | ~1.5d | **4–6h** | Number Match, trend questions | P0 |
| P4 | Retrieve-then-read (section expansion) | 0.5–1d | **~2h** | Narrative accuracy vs cost | P1 |
| — | Features 3, 9c/9d, 5, 7, 2 | ~4d | **10–12h** (Feature 7 tag discovery is ~half) | — | — |

**Core path (P0–P4) with Claude Code: ~16–21 hours ≈ 2.5–3 focused working days**
(vs. roughly 5–6 days manually).

How to read the estimate:
- It is *your* time: prompting, reviewing diffs, running the pipeline and eval, deciding.
- What Claude Code compresses most: boilerplate (BM25 index, RRF, eval metrics, tool-calling
  loop in `qa.py`, tests). What it compresses least: **labelling and verifying the golden set**
  (it can draft questions and propose expected sources from the corpus, but a person must check
  them — this is the asset that convinces leadership), judging eval results, and Feature 7's
  per-company XBRL tag discovery.
- Not included: wall-clock waits (re-embedding after contextual headers, `ragas-real` runs of
  ~5 min each, several runs to average out faithfulness noise) and any surprises from the data.
- Typical sessions: P0 = 2 sessions, P1 = 1, P2 = 1, P3 = 1–2, P4 = 1.


---

## 4. The experiment to show leadership

Once P0 and P1 are in, run three configurations on the same golden set:

1. **Long context only** (single-filing questions only — the others don't fit)
2. **Current RAG** (dense only)
3. **Hybrid + rerank** (+ P2/P3 when available)

Report per category: accuracy, Number Match, citation correctness, refusal accuracy,
cost/query, latency. If long context wins on some single-filing slice, that is a
useful finding (simplify there). On cross-company, multi-year and exact-figure
questions, the numbers should make the case for retrieval on their own.

---

## Sources
- Chroma Research — Context Rot: https://trychroma.com/research/context-rot
- HackerNoon — Long Context Beats RAG on Accuracy (cites Hamilton et al., 2026): https://hackernoon.com/long-context-beats-rag-on-accuracyso-why-keep-retrieval
- From BM25 to Corrective RAG (arXiv 2604.01733): https://arxiv.org/abs/2604.01733
- Long Context vs. RAG for LLMs: An Evaluation and Revisits (arXiv 2501.01880): https://arxiv.org/pdf/2501.01880
- RAG vs. Long Context in 2026 (Towards AI): https://pub.towardsai.net/rag-vs-long-context-in-2026-when-retrieval-still-wins-e6ebad9a4096
