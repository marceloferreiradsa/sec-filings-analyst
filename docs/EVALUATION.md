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

**Status:** Historical — superseded by EV-03

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
P1 is compared against.** *(superseded by EV-03)*

---

## EV-03 — Retrieval after ADR-19 (fiscal calendar, dated headers)

**Status:** Current baseline

**Run:** 2026-10-24 · commit `9232e99` + ADR-19 changes · golden set **82 questions,
70 scored** (+tmp-15, tmp-16: calendar dates on non-calendar fiscal years, added and
reviewed before this run) · config app.

| run | file | what |
|---|---|---|
| before | `retrieval_2026-10-24T173416Z_app.json` | EV-02 code and index, 70 questions |
| fiscal strict | `retrieval_2026-10-24T173517Z_app.json` | labels fixed, year = fiscal only |
| + date exception | `retrieval_2026-10-24T173641Z_app.json` | + calendar year for dates with month |
| **final** | `retrieval_2026-10-24T174141Z_app.json` | + dated period headers |

| category | n | R@5 before | R@5 final | MRR@5 final | R@20 final |
|---|---|---|---|---|---|
| figure | 15 | 1.000 | 1.000 | 0.797 | 1.000 |
| narrative | 15 | 0.267 | 0.267 | 0.189 | 0.667 |
| comparison | 12 | 0.542 | 0.542 | 0.507 | 0.725 |
| trend | 12 | 0.312 | 0.333 | 0.547 | 0.500 |
| temporal | 16 | 0.500 | **0.812** | 0.596 | 0.938 |
| **all** | 70 | 0.532 | **0.607** | 0.528 | 0.781 |

Paired bootstrap, k = 5, before → final: temporal **+0.312 [+0.125, +0.562]**, overall
**+0.075 [+0.014, +0.146]**, both detectable; no category decreases. Intermediate
steps: fiscal strict dropped figure to 0.800 (fig-13, fig-15 are calendar-dated);
the date exception recovered fig-15/tmp-15/tmp-16; the dated header moved fig-13
from rank 9 to 1 with the same candidates.

**Still failing (ranking, not labels — P1 territory):** tmp-02 and tmp-03 ("latest
quarter", ranks 8 and 12), tmp-14 (right 10-Q at rank 1, but the chunk with the
revenue sentence is outside the top 20), fig-03 at rank 5.

**Known undercount (ADR-18)** unchanged. **This is the baseline P1 is compared against.**

---

## EV-04 — P1a: BM25, hybrid (RRF) and contextual headers vs EV-03

**Status:** Measured — not shipped (ADR-21); EV-03 remains the production baseline

**Run:** 2026-10-24 · 70 scored questions · config app · `score.py run --mode …`.
Dense after the refactor is identical to EV-03 chunk by chunk
(`retrieval_2026-10-24T180638Z_app.json`).

| Recall@5 | dense (EV-03) | bm25 | hybrid | dense + headers | hybrid + headers |
|---|---|---|---|---|---|
| figure | 1.000 | 0.933 | 0.933 | 0.600 | 0.867 |
| narrative | 0.267 | 0.600 | 0.467 | 0.533 | 0.533 |
| comparison | 0.542 | 0.408 | 0.625 | 0.333 | 0.333 |
| trend | 0.333 | 0.417 | 0.479 | 0.125 | 0.292 |
| temporal | 0.812 | 0.438 | 0.688 | 0.500 | 0.438 |
| **all** | **0.607** | 0.570 | **0.646** | 0.436 | 0.507 |
| all, Recall@20 | 0.781 | 0.762 | 0.813 | 0.786 | 0.800 |

Files: `…T180643Z_app-bm25`, `…T180648Z_app-hybrid` (no headers); `…T181044Z_app`,
`…T181049Z_app-bm25`, `…T181055Z_app-hybrid` (with headers, reverted). Bootstrap
intervals in ADR-21. Hybrid at k = 20: narrative 0.867 vs dense 0.667 — the
candidate pool for P1b.

---
**Última revisão:** 2026-10-24 · detalhe em `state/changelog.md`
