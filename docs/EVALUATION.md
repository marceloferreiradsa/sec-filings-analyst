# Evaluation results

> **Scope:** this document owns the *measured* evaluation numbers of the RAG system —
> retrieval (P0b) now, generation and long-context (P0c) later. Method and metric
> definitions live in ADR-16; the golden set's design in ADR-15; sources in
> `docs/REFERENCES.md`. Every table carries its run date, commit and result file.

---

## EV-01 — Retrieval baseline, dense-only (P0b)

**Status:** Historical — app column superseded by EV-02

**Run:** 2026-10-24 · commit `4926d1c` · golden set 80 questions, 68 scored (12
out-of-corpus excluded, scored in P0c) · `python eval/golden/score.py run --config …`
· files `eval/results/retrieval_2026-10-24T165428Z_app.json` (app) and
`…T165435Z_plain.json` (plain). Cost: 68 embedding calls (< $0.001).

**Scorer self-check:** oracle run = 1.000 on every metric at every k
(`…T165343Z_oracle.json`); 116 of 119 labels match exactly one chunk, 3 match two.

**Configurations:** *app* = exactly how the Streamlit app calls the retriever
(auto-detected filters, `max_per_company=2` when no company is picked in the
sidebar); *plain* = same, without the per-company cap.

| category | n | app R@5 | app All@5 | app MRR@5 | plain R@5 | plain All@5 | plain MRR@5 | plain nDCG@5 | plain R@20 |
|---|---|---|---|---|---|---|---|---|---|
| figure | 15 | 0.600 | 0.600 | 0.500 | 1.000 | 1.000 | 0.613 | 0.709 | 1.000 |
| narrative | 15 | 0.200 | 0.200 | 0.167 | 0.267 | 0.267 | 0.189 | 0.209 | 0.667 |
| comparison | 12 | 0.542 | 0.333 | 0.524 | 0.542 | 0.333 | 0.524 | 0.457 | 0.725 |
| trend | 12 | 0.125 | 0.000 | 0.375 | 0.312 | 0.000 | 0.454 | 0.298 | 0.479 |
| temporal | 14 | 0.214 | 0.214 | 0.179 | 0.429 | 0.429 | 0.235 | 0.282 | 0.571 |
| **all** | 68 | **0.338** | 0.279 | 0.342 | **0.518** | 0.426 | 0.398 | 0.394 | **0.698** |

R = Recall, All = every expected source found. Full per-k tables: `score.py` output
or the result files.

**app → plain, paired bootstrap (10,000 resamples, 95% CI), k = 5:**
Recall@5 overall **+0.180 [+0.099, +0.268]**, detectable; figure +0.400
[+0.133, +0.667] and trend +0.188 [+0.083, +0.292] detectable; narrative, temporal and
comparison not detectable at this sample size (temporal +0.214 [+0.000, +0.429]).

**Readings** (each with what would make it false):
1. **The app's per-company cap starves single-company questions.** In the app
   configuration 53 of 68 questions received 2 chunks and 3 received 1, although
   `top_k=5`: the cap of 2 per company also applies when the question names one
   company. *False if* the generator's answers on those questions are unaffected —
   to be checked in P0c.
2. **Dense retrieval finds figures but not prose.** Plain: figure R@5 = 1.0, narrative
   0.267 (0.667 at k=20). The answer is often in the top 20 but not the top 5 — the
   gap a reranker (P1b) is meant to close. *False if* P1 hybrid + rerank does not move
   narrative R@5 beyond the CI.
3. **Multi-year trends are never complete:** All@20 = 0 for trend — no question got all
   four years. *False if* the misses turn out to be label gaps (they were not, below).
4. **Temporal questions fail at roughly half the rate of figures** (0.429 vs 1.0 at
   k=5), consistent with the wrong fiscal labels of AB-06 (a). *False if* fixing the
   labels leaves temporal R@5 within its CI.

**Miss review (ADR-16, incomplete labels):** of 45 expected sources missed at k=20
(plain), 3 had their evidence in a chunk with other labels: **nar-02** (same sentence
in NVDA FY2026 10-K §7, not only §1A) and **cmp-10** (same META sentence in the
2025-09-30 10-Q) are plausible correct alternatives; **cmp-02** (AAPL "Operating
Margin: 32.0%") matched GOOGL's summary — a different company, correctly rejected by
the four-field label. 2 of 45 (~4%) is far from "labels dominate the score" (ADR-16's
falsifier). Widening those two labels needs an alternatives field in the schema and
the owner's approval — **declined** (ADR-18).

---

## EV-02 — Retrieval after ADR-17 (app no longer truncates single-company queries)

**Status:** Current baseline

**Run:** 2026-10-24 · commit `f899e05` + ADR-17 change in `rag/retrieve.py` ·
`eval/results/retrieval_2026-10-24T165929Z_app.json` (config app; 0 embedding calls, cached).

The app configuration now scores **identically to EV-01's plain column** on every
metric and k (Recall@5 0.518, Recall@20 0.698; per category as in EV-01 plain).
Paired bootstrap vs EV-01 app, k = 5: Recall@5 +0.180 [+0.099, +0.268], All@5
+0.147 [+0.074, +0.235]. Sanity check: a question naming no company still gets ≤ 2
chunks per company; a question naming Apple now gets 5 Apple chunks.

**Known undercount (ADR-18):** nar-02 and cmp-10 have their evidence also in an
unlabelled chunk; scores are a lower bound. Re-check the share of such misses after
every P1 run (reopen ADR-18 above 5%).

Readings 2–4 of EV-01 stand; reading 1 is resolved by ADR-17. **This is the baseline
P1 is compared against.**

---
**Última revisão:** 2026-10-24 · detalhe em `state/changelog.md`
