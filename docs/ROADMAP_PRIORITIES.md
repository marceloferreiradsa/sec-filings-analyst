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

> **Status (2026-10-24):** golden set done (ADR-15); retrieval scoring done (ADR-16) —
> measured baseline in `docs/EVALUATION.md` (EV-01). Long-context arm and generation
> metrics (P0c) pending.

**Why first:** today's eval measures *generation* (15 assertion cases + RAGAS
faithfulness/relevancy, which `evaluate.py` itself notes varies 0.33–0.94 between runs on
multi-company questions). Nothing measures *whether the right chunk was retrieved*,
so we cannot prove that hybrid search or reranking helps, nor justify any of the
choices below with data.

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
3. **Rerank (Feature 4):** fused top 30–50 → top 5–8, through **hosted APIs in a
   fallback chain** — Cloudflare `bge-reranker-base` → SubQ Snap → no rerank, with an
   explicit notice on the page (ADR-14). Local cross-encoders were measured and
   rejected for the VPS (`experiments/rerank_latency/README.md`).
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
  them — the golden set is the evidence every later decision rests on), judging eval results, and Feature 7's
  per-company XBRL tag discovery.
- Not included: wall-clock waits (re-embedding after contextual headers, `ragas-real` runs of
  ~5 min each, several runs to average out faithfulness noise) and any surprises from the data.
- Typical sessions: P0 = 2 sessions, P1 = 1, P2 = 1, P3 = 1–2, P4 = 1.


---

## 4. The experiment — proof of concept and grounds for each choice

The experiment is not a demo: it is what justifies each component of the system.
It must show **when** a robust hybrid RAG is worth it and when a simpler option is
enough — including the cases where the simpler option wins.

Once P0 and P1 are in, run on the same golden set:

1. **Retrieval variants** — dense only (current), BM25 only, hybrid (RRF), hybrid +
   rerank for each tier of the rerank fallback (see section 5), and no rerank.
2. **Long context vs RAG** — single-filing questions sent whole to a long-context
   model; for cross-company / multi-year questions, document why they do not fit
   (window and cost).
3. **Contextual chunk headers** — with and without.
4. **Generator** — gpt-4o-mini (current) vs cheaper and stronger alternatives, keeping
   temperature=0 (ADR-10).
5. **Latency in the production configuration** (VPS, 2 vCPU).

Report per category: Recall@k / MRR, accuracy, Number Match, citation correctness,
refusal accuracy, cost/query, latency — and **cost per correct answer**, the metric
that says when the extra machinery pays for itself. If long context wins on some
single-filing slice, that is a useful finding (simplify there).

---

## 5. Cost and deploy

**This section is the single place for the roadmap's cost estimates.** Latency
measurements live in `experiments/rerank_latency/README.md`. Prices checked on the
official pricing pages on 2026-10-21/22; token counts measured on
`data/index/chunks.json` (6,396 chunks, mean 283 tokens; a 10-K's indexed sections
median 44k tokens, max 75k; a section median 9.5k, p90 21k).

### Prices used (USD per 1M tokens, input / output)

| Model | Price | Role |
|---|---|---|
| gpt-4o-mini | 0.15 / 0.60 | generator today |
| gpt-4.1-nano | 0.10 / 0.40 | P2 query understanding |
| gpt-4.1-mini | 0.40 / 1.60 | judge; long-context arm (1M window) |
| Gemini 2.5 Flash-Lite | 0.10 / 0.40, free tier | long-context arm alternative (1M window) |
| text-embedding-3-small | 0.02 | embeddings |
| Cloudflare `bge-reranker-base` | 0.003; 10k neurons/day free | rerank tier 1 |
| SubQ `subq-snap-1.1` | 0.04 input, output free; 100M tokens free | rerank tier 2 |

OpenAI Batch is half price — used for the experiment, not for production.
GPT-5-family models are reasoning models (extra output tokens, and temperature=0 is
not available as far as known — to verify before testing them as generator).

### Per query in production

Baseline measured from the code: gpt-4o-mini, top-5, ~1.9k input / ~400 output tokens
≈ **$0.0005**.

| Configuration | $/query | vs today | 100 queries/mo | 1k queries/mo |
|---|---|---|---|---|
| Today | 0.0005 | 1× | $0.05 | $0.50 |
| P1 (BM25 local, rerank via Cloudflare, top-8 to the LLM) | ~0.00065 | 1.3× | $0.07 | $0.65 |
| + P2 router (gpt-4.1-nano) | +0.0001 | | | |
| + P3 tool call (~30% of questions) | +0.00015 avg | | | |
| **P0–P3** | **~0.0009** | **~1.8×** | **$0.09** | **$0.90** |
| + rerank falls to SubQ (tier 2) | +0.00045 | | | |
| + P4 whole sections (30k-token cap) on every question | +0.0045 | ~10× | $0.55 | $5.50 |

P4 is the only item that changes the order of magnitude, so it ships only if P0
shows a gain, and preferably only for narrative questions. One-off costs: re-embedding
with contextual headers ≈ $0.04; BM25 index $0.

*Would be false if* real answers are much longer than ~400 tokens or real traffic
needs more than top-8 — both visible in the app's own logs once P1 ships.

### The experiment (P0)

| Item | Estimate |
|---|---|
| Golden set (~80 questions) drafted by the agent from the corpus, verified by the owner | $0 OpenAI |
| Retrieval metrics (Recall@k, MRR) — only question embeddings | ~$0 |
| ~6 retrieval variants answered by gpt-4o-mini (Batch) | ~$0.25 |
| Judge, gpt-4.1-mini (Batch) | ~$0.35 |
| Long-context arm — 40 single-filing questions (~44k tokens each) | $0.13 (4o-mini, Batch) – $0.35 (4.1-mini, Batch); $0 on Flash-Lite free tier |
| Long-context arm — 20 multi-filing questions (~220k tokens, needs 1M window) | ~$0.90 (4.1-mini, Batch); $0 on Flash-Lite free tier |
| **One full round** | **≈ $2–3** |
| Three rounds to average out judge/faithfulness noise | ≈ $6–9 |

Budget agreed with the owner (2026-10-21): the current $10 OpenAI balance plus up to
$10 more. Rerank calls in the experiment stay inside the Cloudflare and SubQ free
tiers.

### Fits the VPS?

Measured 2026-10-21: Hostinger VPS, AMD EPYC 9354P, 2 vCPU, 8 GB RAM (5.8 GB free),
84 GB disk free; the app container uses 225 MB, its image is 1.01 GB.

| Component | Effect on the VPS |
|---|---|
| BM25 index (6.4k chunks) | tens of MB of RAM; small dependency — fine |
| Rerank via API | no CPU or RAM on the VPS; two more secrets (Cloudflare, SubQ) |
| Local cross-encoder (rejected) | 2–29 s per query and ~2 GB RAM — see the experiment |
| torch in the image (rejected) | image ~3 GB |

---

## Sources
Evaluation-method bibliography (Cranfield, MRR, DPR, FinanceBench, Contextual Retrieval…): `docs/REFERENCES.md`, cited by ADR-16.
- Chroma Research — Context Rot: https://trychroma.com/research/context-rot
- HackerNoon — Long Context Beats RAG on Accuracy (cites Hamilton et al., 2026): https://hackernoon.com/long-context-beats-rag-on-accuracyso-why-keep-retrieval
- From BM25 to Corrective RAG (arXiv 2604.01733): https://arxiv.org/abs/2604.01733
- Long Context vs. RAG for LLMs: An Evaluation and Revisits (arXiv 2501.01880): https://arxiv.org/pdf/2501.01880
- RAG vs. Long Context in 2026 (Towards AI): https://pub.towardsai.net/rag-vs-long-context-in-2026-when-retrieval-still-wins-e6ebad9a4096
- OpenAI pricing: https://developers.openai.com/api/docs/pricing
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Cloudflare Workers AI pricing: https://developers.cloudflare.com/workers-ai/platform/pricing/
- SubQ models and pricing: https://docs.subq.ai/using-the-api/models/
