# Architectural Decisions — SEC Filings RAG System

This document summarises the eleven architectural decisions made during the
design and build of the SEC Filings RAG system. Each entry covers what was
decided, why, what was rejected, the tradeoff accepted, and a suggested
framing for technical interviews. Later records follow the same format: ADR-12
(how the project is run) and ADR-13 onwards (the improvement roadmap), at the end.

**Project:** Retrieval-augmented Q&A over 10-K and 10-Q SEC filings  
**Companies:** Apple (AAPL), Alphabet/Google (GOOGL), Meta (META), Microsoft (MSFT), NVIDIA (NVDA)  
**Stack:** Python · FAISS · OpenAI Embeddings · GPT-4o-mini · Streamlit

---

## Quick Reference

| # | Decision | The key insight |
|---|----------|----------------|
| 1 | Two-track ingestion | Numbers via certified XBRL API; narrative via HTML parser |
| 2 | Section selection | Index sections that answer analytical questions; exclude administrative ones |
| 3 | Natural-language rendering | Pre-compute at ingestion what users will ask about at retrieval time |
| 4 | ASC 606 combine strategy | Tag renames of the same concept are safe to pool; different-scope candidates are not |
| 5 | period_end over fy field | fy identifies the filing, not the period — derive fiscal year from the date itself |
| 6 | frame as dedup preference | The SEC's own canonical entry wins; most-recently-filed is the fallback |
| 7 | IndexFlatIP | Exact search costs nothing extra at our scale; approximation trades accuracy for imperceptible speed |
| 8 | Post-filter with amplification | IDSelector API is fragile; flat index searches all vectors anyway |
| 9 | Per-company retrieval | Combined multi-company search is asymmetric; separate calibrated searches ensure equal representation |
| 10 | Temperature=0 | Determinism and citation accuracy over variety in financial Q&A |
| 11 | Grounding prompt | Five rules that together prevent hallucination, enforce traceability, and handle limitations honestly |
| 13 | Evidence-driven roadmap | Every component must earn its place with retrieval metrics and cost per correct answer, on the hardware it runs on |
| 14 | Rerank via API fallback chain | Measure before choosing; degrade visibly to hybrid search instead of failing |
| 15 | Golden set labelled by section + evidence | Labels survive re-chunking; every evidence checked against the corpus before review |
| 16 | Deterministic retrieval scoring | Recall@k / MRR / nDCG by evidence match, with confidence intervals; no LLM judge for retrieval |
| 17 | Per-company cap ignored for single-company queries | A balancing cap must not truncate a query that already names one company |
| 18 | Golden-set labels not widened after scoring | A score biased low is preferable to one inflated by post-hoc relabelling |
| 19 | Fiscal calendar per company; dated period headers | A year means the fiscal year; a date with a month means the calendar period; summaries say both |
| 20 | Versioned releases shown in the app | Visitors see what changed and how it was measured; the version lives only in CHANGELOG.md |
| 21 | Hybrid retrieval built, held back until rerank | BM25 + RRF helps prose and trends but costs period questions; ship it only as the reranker's candidate pool |
| 22 | Dense + SubQ Snap rerank; fallback to dense with notice | The measured best: Recall@5 0.607 → 0.811; Cloudflare and BM25 dropped for adding nothing |

---

## ADR-01 — Two-track ingestion (XBRL + HTML)

**Status:** Active

### What was decided
Two separate ingestion pipelines run in parallel. Track A fetches structured
financial data from the SEC's XBRL API at `data.sec.gov`. Track B downloads
and parses the HTML filing documents to extract narrative sections.

### Why
**Track A (XBRL):** Financial values in XBRL are certified by the company under
legal obligation, validated by the SEC, and available as machine-readable JSON.
The API provides historical depth going back to 2009 without additional
downloads. Extracting the same numbers from HTML tables introduces parsing risk,
unit inconsistencies (some companies report in thousands, others in billions),
and colspan/rowspan layout complexity. The XBRL route eliminates all of this.

**Track B (HTML):** Risk Factors, MD&A, and Business sections are narrative text
that XBRL does not tag. Management's strategic commentary, competitive framing,
and forward-looking language live only in the HTML filing.

### What was rejected
Single-track HTML parsing of everything including tables. This is the common
tutorial approach. It fails for financial data because: table extraction from
SEC HTML is unreliable, extracted numbers lack unit consistency, and the
resulting text does not embed well semantically.

### Tradeoff accepted
XBRL only covers tagged line items. Footnote detail, segment breakdowns, and
management commentary on specific numbers are only in Track B. The system
answers "what was the revenue?" from Track A and "why did revenue grow?" from
Track B, but cannot answer questions that require both simultaneously from a
single chunk.

### Connection to BI background
Track A is the fact table — precise, certified, numeric. Track B is the
descriptive dimension — context and narrative. They converge on a shared
metadata schema the same way a star schema converges on shared keys.

> **Interview framing:**
> *"I designed a two-track ingestion pipeline. Track A uses the SEC's XBRL API
> to fetch certified financial values — the same numbers the company filed under
> legal obligation, no parsing required. Track B parses the HTML filings for
> narrative sections that XBRL doesn't cover. The two tracks serve different
> query types: Track A for precise figures, Track B for strategic context. The
> alternative — parsing everything from HTML including tables — is the tutorial
> approach, but financial tables in SEC filings have layout complexity that makes
> extraction unreliable, and the extracted numbers don't embed well semantically."*

---

## ADR-02 — Section selection for indexing

**Status:** Active

### What was decided
**10-K:** Items 1 (Business), 1A (Risk Factors), 7 (MD&A)  
**10-Q:** Items 2 (MD&A), 1A (Risk Factors)  
Everything else excluded, including Item 8 (Financial Statements), Item 2
(Properties), Item 3 (Legal Proceedings), and Item 9A (Controls).

### Why
Every chunk in the index competes with every other chunk during retrieval.
Including low-signal sections (Properties: a list of offices; Controls:
compliance boilerplate) creates false positives — chunks that score above
threshold but add nothing to the answer. The selected sections answer analytical
questions. The excluded sections answer administrative questions.

Item 8 (Financial Statements) is excluded because Track A handles financial
data more cleanly via XBRL. Including the HTML tables would create noisy text
that partially overlaps with Track A's structured summaries, confusing the
retriever.

### What was rejected
Index everything and let the retriever sort it out. This degrades precision
because administrative sections contain vocabulary that partially overlaps
with analytical content without adding signal.

### Extensibility
`SECTIONS_TO_INDEX` in `html_parser.py` is the single control point. Adding
a section is one string addition. Re-running the pipeline forward from
`ingest.py` picks up the change. Raw downloaded filings are never modified.
Planned improvement: move this constant to `config.yaml` for code-free
configuration (Feature 3 in NEXT_FEATURES.md).

### Tradeoff accepted
Some information is not in the corpus. Item 7A (quantitative market risk
tables) contains derivative exposure data a specialist analyst might want.
The decision was that the precision gain from excluding it outweighs the
occasional missed specialist query.

> **Interview framing:**
> *"I treated the SEC filing structure as domain knowledge. Every company files
> the same items in the same order by regulatory mandate, which gives you a
> reliable content map. I indexed the sections that answer analytical questions
> and excluded the sections that answer administrative questions. Financial
> statements are excluded from Track B because Track A handles them better via
> XBRL. The control is a single set in one file — adding or removing a section
> is one string change followed by a pipeline re-run."*

---

## ADR-03 — Natural-language rendering of XBRL numbers

**Status:** Active

### What was decided
Raw XBRL values are transformed into formatted natural-language summaries
before embedding. `60922000000` becomes `Revenue: $60.92B`. Margins are
computed from raw values and included explicitly: `Gross Margin: 72.7%`.

### Why
Embedding models map text to positions in semantic space based on patterns
learned from training data. A 10-digit integer (`60922000000`) is tokenised
as digit fragments with no reliable semantic position. The model has never
seen that specific integer in meaningful financial context.

The phrase "Revenue grew 126% year-over-year to $60.9B" has been seen
thousands of times in financial text during training. It has a well-defined
position in semantic space near queries about revenue performance. Semantic
retrieval works on meaning, not numeric value.

**Derived metrics are the most valuable transformation.** XBRL provides revenue
and gross profit as separate values. Gross margin is computed from them and
embedded explicitly because analysts ask about margins directly. The principle:
pre-compute at ingestion what users will ask about at retrieval time.

### What was rejected
Embedding raw numbers directly. This approach fails because the embedding
model has no mechanism to learn that `60922000000` is semantically near
"strong revenue performance."

### Tradeoff accepted
Natural-language rendering makes pure arithmetic less convenient — the LLM
must parse "$60.92B" back to a number for calculations. For retrieval and
synthesis this tradeoff is correct. For direct calculation queries, the
hybrid retrieval sidecar (Feature 1 in NEXT_FEATURES.md) would provide raw
values on demand.

### Connection to BI background
Equivalent to computing measures (margins, growth rates) at ingestion time
rather than at query time — the same principle as pre-computing DAX measures
instead of calculating them per-report.

> **Interview framing:**
> *"I knew the embedding model handles labelled ratios and formatted values
> better than raw integers, so I pre-computed margins and formatted values in
> billions at ingestion time. The goal was to make financial data retrievable
> by semantic meaning rather than exact numeric match. I also derived metrics
> the XBRL data doesn't explicitly provide — gross margin, operating margin,
> R&D as a percentage of revenue — because I knew those are what analysts
> actually ask about. The principle is: pre-compute at ingestion what users
> will ask about at retrieval time."*

---

## ADR-04 — ASC 606 combine strategy for revenue tags

**Status:** Active

### What was decided
For metrics in `COMBINE_STRATEGY_METRICS = {"revenue", "net_income"}`, entries
from all candidate XBRL tags are pooled before deduplication. For all other
metrics, first-match-wins is used.

### Why
The ASC 606 accounting standard change in 2018 introduced a new XBRL tag for
revenue: `RevenueFromContractWithCustomerExcludingAssessedTax`. Companies
migrating to ASC 606 stopped filing under the legacy `Revenues` tag and
switched to the new one. The two tags are renames of the same economic concept.

With first-match on `Revenues`, the code returned pre-2018 data for MSFT,
META, and AAPL. Their modern periods (FY2022–FY2025) had all metrics except
revenue, causing the `if not rev: continue` guard to filter them out. Zero
summaries were built for those three companies. No error was raised.

Pooling all candidates and deduplicating by `period_end` (most-recently-filed
wins) produces a complete time series regardless of which tag the company
used for each period.

### Why not combine everything
Cash candidates have different economic scopes. For MSFT in the same period:
`CashCashEquivalentsAndShortTermInvestments` = $94.5B (cash + investments);
`CashAndCashEquivalentsAtCarryingValue` = $30.2B (cash only). Pooling these
and deduplicating would mix definitions inconsistently across periods.
First-match-wins preserves definitional consistency.

### The diagnostic process
`diagnose_xbrl.py` was written to reveal which tags each company actually
uses and what date ranges they cover. The tag-timeline asymmetry was
immediately visible in the output, leading directly to the fix.

> **Interview framing:**
> *"During testing, three of five companies returned zero financial summaries
> with no error. A diagnostic revealed the cause: the ASC 606 accounting
> standard change split the revenue concept across two XBRL tags, with
> different companies adopting the new tag at different times. My first-match
> approach returned only pre-2018 data for those companies. I fixed it by
> pooling entries across all candidate tags before deduplication — safe for
> revenue because the tags are renames of the same concept, not safe for cash
> where the candidates have genuinely different scopes. The bug had no bad
> code in it. An external accounting standard change invalidated the assumption
> that companies use one tag consistently."*

---

## ADR-05 — period_end over the fy field for period identification

**Status:** Active

### What was decided
The `fy` field from XBRL entries is not used for period identification.
`fiscal_year` is derived as `int(period_end[:4])`. Period buckets are keyed
by `period_end` alone.

### Why
The `fy` field does not mean "the fiscal year this period belongs to." It
means "the fiscal year of the most recent filing that reported this value."
These are different because:

- 10-K income statements cover 3 years (current + 2 prior comparatives)
- 10-K balance sheets cover 2 years (current + 1 prior comparative)

Our dedup keeps the most-recently-filed entry per period. For revenue
(income statement), the FY2024 value last appeared as a 2-year-prior
comparative in the FY2026 10-K → `fy=2026`. For cash (balance sheet), the
FY2024 value last appeared as the prior-year in the FY2025 10-K → `fy=2025`.
Same date, two different `fy` values, two different buckets. One bucket had
revenue, no cash. The other had cash, no revenue. The one without revenue was
filtered out. Result: 3 summaries instead of 4 with no error.

The `period_end` ISO date is a physical fact about the period itself. It
cannot be distorted by the filing context it came from.

### Discovery
`diagnose_periods.py` output showed the fragmentation directly: the same
`period_end=2024-01-28` appearing under `fy=2025` and `fy=2026` in separate
buckets for the same company.

> **Interview framing:**
> *"I found that the fy field in XBRL entries doesn't identify the period — it
> identifies the most recent filing that reported the value as a comparative.
> Because income statements cover three years and balance sheets cover two,
> our deduplication strategy picked entries from different filing vintages for
> different metrics. The same balance-sheet date appeared under fy=2025 while
> the income statement date appeared under fy=2026. The compound key split them
> into different buckets, causing period fragmentation. The fix was to stop
> trusting fy entirely and derive fiscal year from the ISO date of period_end,
> which is a physical fact about the period itself and cannot be distorted by
> filing context."*

---

## ADR-06 — frame field as deduplication preference

**Status:** Active

### What was decided
When multiple entries exist for the same `period_end`, prefer the one carrying
a valid `frame` value (e.g. `CY2024`, `CY2024Q3`, `CY2024Q3I`). Fall back to
most-recently-filed when no frame entry exists.

### Why
The SEC assigns `frame` values to entries it considers canonical for a given
calendar period. When it is present, it represents the SEC's own selection
— a stronger authority than most-recently-filed. The pattern
`CY\d{4}(Q[1-4])?I?` identifies valid frame values.

**Side benefit for quarterly data:** The SEC's ±30 day tolerance for quarterly
frames (91 days) never fits year-to-date entries (a Q3 YTD entry spans ~273
days). YTD entries never receive a frame. Quarter-only entries do. The frame
preference therefore naturally selects quarter-only over YTD entries when both
exist for the same period_end — without any explicit YTD-detection logic.

### Why frame is not always present
Frame is absent on amended filings, filings pre-dating the frames system,
and any entry whose period doesn't align within the tolerance window.
The most-recently-filed fallback handles these cases.

### What frame is NOT used for
The year notation in frame values (CY2024, CY2025) is calendar-based, not
fiscal-year-based. For NVIDIA, whose fiscal year ends in January, FY2026 data
carries `frame=CY2026`. We do not read that year as the fiscal year — fiscal
year continues to be derived from `period_end` (Decision 5).

> **Interview framing:**
> *"The SEC assigns a frame field to entries it considers canonical for a given
> calendar period. I use it as a deduplication preference: frame-bearing entries
> win; most-recently-filed is the fallback for the ~30-40% of entries without a
> frame. There is a useful side effect: the SEC's quarterly frame tolerance of
> ±30 days around 91 days never fits year-to-date entries, so the frame
> preference naturally selects quarter-only over YTD entries without any
> explicit YTD detection. I do not use the frame's year notation as the fiscal
> year — that continues to be derived from the period_end date."*

---

## ADR-07 — IndexFlatIP over approximate indexes (IVF, HNSW)

**Status:** Active

### What was decided
FAISS IndexFlatIP: exact inner product search over all 6,396 vectors.

### Why
At 6,396 vectors, the FAISS search takes under 2ms. The query bottleneck is
the embedding API call (~400ms) and LLM generation (~3–8s). Approximate
indexes like IVF and HNSW trade retrieval accuracy for speed — a speed the
user cannot perceive at our scale.

**Why inner product, not L2 distance:** Our embeddings have unit norm
(confirmed empirically: mean = 1.0000). For unit-norm vectors,
`inner_product(a, b) = cosine_similarity(a, b)`. We get semantic angle
similarity — direction regardless of magnitude — at the computational cost
of a dot product.

**Why exact matters for RAG:** An approximate index cannot guarantee returning
the true nearest neighbors. Missed relevant chunks directly degrade answer
quality. At our scale there is no justification for accepting accuracy loss.

### What was rejected
**IVFFlat:** Clusters vectors into Voronoi cells and searches only nearby cells.
Requires training and hyperparameter tuning (number of clusters, cells to
search at query time). Adds complexity in exchange for a speedup that doesn't
matter.

**HNSW:** Graph-based approximate search. No training needed but uses more
memory and introduces approximation errors. Same conclusion: not justified
at this scale.

### Threshold for reconsidering
Approximately 100,000 vectors — roughly scaling to all S&P 500 companies
over ten years. At that scale, exact search starts taking tens of
milliseconds and approximate indexing becomes worthwhile.

### Important implication
Because IndexFlatIP always computes all inner products regardless of k,
requesting `n_candidates = index.ntotal` costs nothing extra compared to
requesting `n_candidates = 180`. This is the basis for the post-filter fix
(Decision 8).

> **Interview framing:**
> *"I used exact search because at 6,396 vectors FAISS takes under 2ms, which
> is negligible compared to the embedding API call and LLM generation. Switching
> to an approximate index like HNSW or IVF would trade retrieval accuracy for a
> speedup the user cannot perceive. The threshold where approximate indexing is
> justified is around 100,000 vectors — roughly scaling to the full S&P 500
> over ten years. The choice of inner product follows from unit-norm embeddings:
> inner product on unit-norm vectors is mathematically equivalent to cosine
> similarity, so we measure semantic direction without penalising shorter
> chunks."*

---

## ADR-08 — Post-filter with amplification over FAISS IDSelector

**Status:** Active

### What was decided
Retrieve `n_candidates = index.ntotal` candidates from FAISS, filter by
metadata, stop when `top_k` matches are found. Apply `max_per_company`
cap within the filtered results.

### Why
FAISS has no native metadata filtering. Three options existed:

1. **Sub-index rebuild** — extract valid vectors, build temporary index, search.
   Expensive per query, adds latency proportional to filter selectivity.

2. **IDSelectorBatch** — FAISS-native API that constrains search to specific
   vector IDs. Conceptually correct but Python bindings are inconsistent
   across FAISS CPU versions; `search_with_params` is not available on all
   index types in all versions; errors produce silent failures or segfaults
   rather than exceptions.

3. **Post-filter with amplification** — retrieve all candidates, filter
   afterward. Uses only the stable `index.search()` call.

**Why `n_candidates = index.ntotal` is correct:** For IndexFlatIP, all inner
products are computed regardless of k. Requesting all n candidates costs
nothing extra in computation. The only overhead is sorting 6,396 elements
instead of 180 — microseconds. This guarantees every matching chunk is
visible to the post-filter step, regardless of how sparse the category is.

Earlier `FILTER_AMPLIFICATION = 15` was insufficient: financial data
represents 0.6% of the index (40/6,396). With top_k=12, amplification=15
only inspected 180 candidates (~3% of the index), missing most financial
summaries for non-dominant companies.

### Tradeoff accepted
Slightly more data passes through the filter step than necessary. At our
scale this is invisible.

> **Interview framing:**
> *"FAISS doesn't support metadata filtering natively. The FAISS-native approach
> is IDSelectorBatch, which constrains search to specific vector IDs, but the
> Python bindings are inconsistent across versions and require careful pointer
> handling. I used post-filtering instead: retrieve all candidates using the
> stable search call, filter by metadata, stop when top_k matches are found.
> Because IndexFlatIP always computes all inner products regardless of k,
> requesting all candidates costs nothing extra in computation. This also solved
> a subtle bug where sparse categories like financial summaries (0.6% of the
> index) fell below any fixed amplification threshold."*

---

## ADR-09 — Per-company retrieval for multi-company queries

**Status:** Active

### What was decided
When `active_filters.company` contains two or more tickers, run a separate
similarity search for each company, merge results by score, return top_k.

### Why
Combined multi-company search produces asymmetric results. When a user asks
"how did Microsoft and Google describe cloud competition?", MSFT's language
about Azure competition scores higher for that query phrasing than GOOGL's
language about the same topic. A combined search returned six MSFT chunks
and zero GOOGL chunks — confirmed empirically.

The asymmetry is intrinsic to how the two companies write about the same
topic. It cannot be fixed by adjusting amplification or thresholds. Only
running independent calibrated searches per company guarantees each
contributes its best content.

**The score gap is information, not a problem.** After merging, MSFT might
occupy ranks 1–3 at scores ~0.63 and GOOGL ranks 4–6 at scores ~0.53.
This tells the LLM that MSFT's content is more directly on-topic for that
specific phrasing — which is true and useful for synthesis.

### Known inefficiency
Each company sub-retrieval currently re-embeds the query independently.
For a 5-company query this means 5 embedding API calls for the same question,
adding ~1.5 seconds of unnecessary latency. The fix is to embed once in
`_retrieve_per_company()` and pass the vector to each sub-retrieval. This
is a clean refactor not yet implemented.

### How it differs from max_per_company
`max_per_company` enforces balance within a post-filter step — best for
"all companies, filtered by category" queries.
Per-company retrieval runs independent calibrated searches — best for
"compare company A and company B" queries where equal representation must
be guaranteed regardless of relative scoring.

> **Interview framing:**
> *"When a query names multiple companies, a combined search can produce
> asymmetric results — the company whose vocabulary is more semantically aligned
> with the query phrasing dominates all result slots. I run separate searches
> per company and merge by score. This guarantees each company contributes its
> best content while preserving the score gap that tells the LLM which company's
> material is more directly on-topic. The known inefficiency is that the current
> implementation re-embeds the query once per company — a trivial refactor would
> embed once and reuse the vector."*

---

## ADR-10 — Temperature=0 for the generator

**Status:** Active

### What was decided
GPT-4o-mini is called with `temperature=0` for all queries.

### Why
**Determinism:** Financial analysis requires consistent answers. The same
question should produce the same answer every time. Temperature=0 ensures
the model always selects the highest-probability token, producing
essentially identical outputs for identical inputs.

**Citation accuracy:** Higher temperatures increase the probability of
slightly wrong citations — citing FY2025 when FY2024 was retrieved, or
combining figures from different periods. For source-traceable financial
analysis, this is unacceptable.

**The grounding prompt and temperature=0 work as a pair.** The grounding
prompt constrains the input space ("answer only from the retrieved context").
Temperature=0 constrains the output space ("always pick the most probable
token given that constrained input"). Together they prevent both content
hallucination and expression variance.

**Debugging:** At temperature=0, failures are reproducible. A wrong answer
is consistently wrong, traceable cleanly to retrieval quality or prompt
quality without the confound of sampling randomness.

### When higher temperature would be appropriate
Creative writing, brainstorming, conversational systems where variety feels
natural, or synthesis tasks where multiple valid framings exist and any of
them would be acceptable. None of these apply to factual financial Q&A.

> **Interview framing:**
> *"Temperature=0 was chosen for determinism and citation accuracy. When a
> question has a factual answer grounded in retrieved passages, the model should
> consistently produce that same answer. Higher temperature introduces sampling
> variance that serves no purpose when the output is constrained by the grounding
> prompt anyway — and increases the risk of slightly wrong citations or
> approximated numbers on edge cases. The grounding prompt and temperature=0
> work together: the prompt restricts what the model is allowed to say, and
> temperature=0 ensures it says it the same way every time."*

---

## ADR-11 — Grounding prompt design

**Status:** Active

### What was decided
A five-rule system prompt that constrains the LLM to the retrieved context,
enforces inline citations, requires temporal and unit precision, demands
explicit treatment of each company in comparisons, and structures honest
limitation responses.

### Why each rule was written as it was

**Rule 1 — "Answer based ONLY on the provided excerpts."** The word "ONLY"
is emphatic by design. Without it, models seamlessly supplement retrieved
context with training knowledge in ways indistinguishable to the user.
"If it is not in the excerpts, it is not in your answer" states the positive
constraint explicitly.

**Rule 2 — Inline citations in exact format.** "For every factual claim"
not "for important claims." Every one. Inline placement (not a references
list at the end) makes it immediately clear which part of the answer is
supported by which source. The format `[COMPANY FILING PERIOD SECTION]`
was designed around the metadata schema — every chunk carries all four
fields so the LLM can always produce a complete citation from what it received.

**Rule 3 — Units and time periods.** A revenue figure without a fiscal
period is meaningless or misleading in financial analysis. This rule forces
explicitness on both dimensions every time.

**Rule 4 — Address each company explicitly.** Prevents "Microsoft has grown
faster than its peers" — a claim that provides no information about the peers.
Comparative questions require explicit treatment of every named party.

**Rule 5 — Honest limitation handling.** The three-part structure: say so
clearly using the specific phrase, explain what information would be needed,
do not invent or estimate. The specific phrase "The provided context does not
contain enough information" creates a recognisable signal distinguishing a
corpus limitation from a system failure, and tells the user the limitation
is about what was retrieved, not about system capability.

### What the prompt does not prevent
Citation errors when multiple years of the same company are in context
simultaneously (the model may cite FY2024 as "most recent" when FY2025 is
also present). The "latest" temporal problem (no way to know which chunk is
most recent from prompt alone). These are retrieval architecture limitations,
not prompt limitations.

### Stress tests passed
- "What will NVIDIA's revenue be in FY2027?" → correct refusal, no speculation
- "What was NVIDIA's revenue for calendar year 2025?" → correct identification
  of the mismatch between fiscal and calendar year
- Test 4 (Apple missing from context) → correct acknowledgment of gap with
  explanation of what was missing

> **Interview framing:**
> *"The system prompt has five rules designed to work together. The grounding
> rule and the honest limitation rule are the most critical — they prevent the
> model from mixing retrieved facts with training knowledge and from hiding
> uncertainty behind plausible-sounding extrapolations. The citation format was
> designed around the metadata schema so every claim traces to an exact chunk.
> I verified the grounding by testing questions the corpus cannot answer and
> confirming the model refused to speculate rather than interpolate. The prompt's
> limits are clearly in the retrieval layer — it governs generation faithfully,
> but it cannot fix what the retriever fails to provide."*

---

## What this system demonstrates for AI Engineering roles

Taken together, the eleven decisions show:

1. **Domain expertise applied to data engineering** — understanding SEC filing
   structure, XBRL taxonomy conventions, and accounting standard changes
   informed every pipeline decision

2. **Diagnostic-first engineering** — three separate diagnostic scripts were
   built to discover root causes (tag transitions, period fragmentation, section
   indexing) before fixes were written

3. **Principled tradeoff reasoning** — every choice has a named alternative
   that was rejected, a cost it accepts, and a threshold at which the decision
   should be revisited

4. **Production-aware design** — extensibility (config file, pipeline
   re-runnability), cost awareness ($0.00175 for five comprehensive analyses),
   and known limitation documentation throughout

5. **Retrieval and generation as separate concerns** — the pipeline is designed
   so each layer can be changed independently; the retrieval layer does not
   depend on the generation layer, and vice versa

---

## Project process decisions

The eleven decisions above are about the system. The records below are about how the
project itself is run, and are kept apart so the narrative above stays about the system.

## ADR-12 — Continuity-method make targets live in `metodo.mk`, with colliding names renamed

**Status:** Superseded — on 2026-10-25 the method left `make` altogether (`python -m metodo <command>`, in `metodo/`); `metodo.mk` was removed and the `Makefile` belongs only to the project

### Context (2026-10-20)
The project adopted the `ai-project-framework` continuity method (`CLAUDE.md`, `state/`,
`docs/_index.md`, `tools/`). The method ships its own `Makefile`, and five of its target
names already exist here with a different meaning:

| Name | In this project | In the method |
|---|---|---|
| `check` | build → run → test → stop the Docker image | check that the docs index is fresh |
| `index` | build the FAISS index | regenerate `docs/_index.md` |
| `clean` | **delete `data/raw` and `data/processed`** | remove Python caches |
| `test` | run the 20 checks against the running container | run the method's own harness |
| `help` | this project's help (default target) | the method's help |

The method's `CLAUDE.md` tells the agent to run `make check` before every action and
`make index` after every record change. Copied as-is, an agent following it would start
a container on every step, and a `make clean` would delete data whose regeneration costs
paid API calls (embeddings).

### What was decided
- The method's targets live in `metodo.mk`, included by the **last** line of the
  `Makefile`. It is last because the first target read becomes the default of a bare
  `make`, and the default here stays this project's `help`.
- The colliding names were renamed **on the method's side**: `check` → `docs-check`,
  `index` → `docs-index`, `help` → `metodo-help`, `test` → `metodo-test`,
  `clean` → `metodo-clean`.
- The 36 citations of those targets in the method's copies (`CLAUDE.md`, `COMO-ADOTAR.md`,
  `tools/`, `.template/`, `refs/README.md`) were rewritten to the new names by script,
  with the citation count kept as an invariant.

This is the same solution as the sibling project `constituicao-stf` (its ADR-14), plus
`check`, which does not collide there.

### What was rejected
Renaming this project's targets (`index` → `faiss-index`, etc.). It would keep the method
untouched but change a workflow that is already in use and in the docs. The project owns
the short names; the method is the guest.

### Tradeoff accepted
The two sibling projects now use different names for the same method command (`check`
there, `docs-check` here). Bringing in a new framework version means redoing the rename.
A uniform prefix for every method target has been proposed upstream (proposal 14 in the
framework's proposal file). When it ships, this ADR is superseded and both projects
migrate.

### Would be false if
A method script read the `Makefile` or called `make <target>` through a subprocess. It
would then trigger this project's target. None does today: checked by grep in `tools/`
on 2026-10-20. Re-check on every framework update.

---

## Roadmap decisions

The records below govern the improvement roadmap (`docs/ROADMAP_PRIORITIES.md`).

## ADR-13 — Adopt the evidence-driven roadmap, under VPS and budget constraints

**Status:** Active

### Context (2026-10-20 → 22)
`docs/ROADMAP_PRIORITIES.md` was drafted outside the project and re-orders
`NEXT_FEATURES.md` around one question: *why retrieval, if context windows are huge?*
Its premises were checked against the code on 2026-10-21: dense-only retrieval (true),
6,396 chunks ≈ 1.82M tokens (true), no retrieval-level evaluation (true),
"`sentence-transformers` is already in the image" (**false** — dev-only; torch would
bring the image from ~400 MB to ~3 GB).

### What was decided
- **The roadmap is adopted as a whole:** P0 retrieval eval + long-context baseline →
  P1 hybrid + rerank + contextual headers → P2 query understanding → P3 XBRL as a tool
  → P4 retrieve-then-read. It supersedes the *Recommended implementation order* of
  `NEXT_FEATURES.md`; each FEAT now carries the priority it maps to.
- **Constraint 1 — production must run on the current VPS** (2 vCPU EPYC, 8 GB) with
  an image without torch. A component that does not fit runs as a hosted API or does
  not ship.
- **Constraint 2 — budget:** the current $10 OpenAI balance plus up to $10 more for
  the experiment. Cost estimates live only in §5 of the roadmap.
- **The experiment is a proof of concept, not a pitch:** it must show *when* the
  robust hybrid RAG is worth it and when a simpler option is enough, reporting cost
  per correct answer.
- P4 ships only if P0 shows a gain that justifies its ~10× cost per query.

### What was rejected
- **The previous order** (FEAT-03 → 9a/9b → 4 → …): it improves UX first and cannot
  prove any quality gain, because nothing measured retrieval.
- **Building the features without P0:** every later choice would rest on intuition.

### Tradeoff accepted
P0 delays visible features by ~2 sessions, and its golden set needs human review —
the slowest part of the roadmap.

### Would be false if
P0 shows retrieval variants are indistinguishable on this corpus — then the hybrid
and rerank work loses its justification and the roadmap must be re-ordered again.

> **Interview framing:**
> *"Before adding hybrid search or reranking, I built a retrieval-level evaluation
> with a golden set and a long-context baseline, so every component had to earn its
> place with Recall@k and cost per correct answer, measured on the hardware it would
> run on."*

---

## ADR-14 — Rerank through hosted APIs in a fallback chain; local cross-encoders rejected

**Status:** Active — provider order revised by ADR-22

### Context
P1 adds a reranker over the fused BM25 + dense candidates (40 → top 5–8). The owner's
first rule (2026-10-21) was *local by default, API only if local is not viable*, with a
criterion approved **before** measuring: VPS, 2 threads, 40 candidates, p95 ≤ 1.0 s
viable; ≤ 2.0 s viable with a trade-off.

### What was measured
`experiments/rerank_latency/README.md`, 2026-10-21/22:
- **Local on the VPS** (fastembed / ONNX, no torch), p95 at n=40, 2 threads: MiniLM-L6
  3.2 s, jina-tiny 3.3 s, bge-base 29 s; ~2 GB RAM peak in every case.
- **Hosted, called from the VPS**, n=40, 30 reps: Cloudflare bge-base p50 0.68 s /
  p95 1.30 s, 0/60 errors; SubQ Snap p50 0.33 s / p95 0.47 s, 0/60 errors (3/60
  intermittent HTTP 403 from the local machine).

### What was decided
Three tiers, each with a timeout:
1. **Cloudflare Workers AI `@cf/baai/bge-reranker-base`** — a real cross-encoder; free
   quota renews daily (~2,900 queries/day estimated, unverified).
2. **SubQ `subq-snap-1.1`** (Decisions API, one yes/no question per passage) — ~2×
   faster, ~$0.00045/query, covered by the owner's credit; public preview.
3. **No rerank** — the fused BM25 + dense order, with an **explicit notice on the page**.

The app logs which tier answered each query. The tier order may be revisited if P0
measures a quality difference.

### What was rejected
- **Local cross-encoder on the VPS:** no model met the criterion at 40 candidates;
  only "viable with a trade-off" at 20. The same bge-base takes 19 s p50 locally vs
  0.66 s through the API. *Not tested:* int8 quantization, 256-token truncation,
  smaller batches — they could narrow the gap, not close a 30× one.
- **torch-based cross-encoder:** ~3 GB image.
- **Cohere, Pinecone, Together, Mixedbread:** no usable per-call pricing or no free tier.
- **Voyage, Jina, ZeroEntropy:** viable, not tested — two tiers plus no-rerank cover
  the failure modes at demo traffic.
- **Reranking with the generator LLM:** slower and pricier than either API.

### Tradeoff accepted
Two external dependencies and two more secrets on the VPS; rerank quality depends on
third parties, and a preview model can change. Silent degradation is prevented by the
notice and the per-query log.

### Would be false if
P0 shows reranking adds little over hybrid retrieval without rerank — the chain would
then be complexity without return, and tier 3 alone would be the right design.

> **Interview framing:**
> *"I set the latency criterion before measuring, benchmarked five local
> cross-encoders on the production VPS and two hosted APIs, and chose a fallback chain
> where the system degrades visibly to hybrid search without reranking instead of
> failing."*

---

## ADR-15 — Golden set labelled by section + literal evidence, not chunk IDs

**Status:** Active

### Context (2026-10-23)
P0 needs a golden set (~80 questions, six categories: figure, narrative, comparison,
trend, temporal, out-of-corpus) whose labels say where the answer is, so retrieval can
be scored with Recall@k / MRR. P1 will change chunk text (contextual headers) and may
change chunking.

### What was decided
- Each expected source is `company · filing_type · period_end · section` plus an
  **evidence phrase copied literally** from the filing. A retrieved chunk counts as
  relevant if it matches the four fields and contains the evidence (whitespace
  collapsed).
- Figure questions carry `expected_figure`: the exact value as it appears in the
  evidence, plus accepted roundings.
- File: `eval/golden/golden_set.jsonl`; `eval/golden/validate.py` must pass before
  review — every evidence found in the corpus, every rounding within 0.05 of the exact
  value. Each question has `reviewed`, set to true only by the owner.
- The agent drafts from the corpus (no API cost); the owner reviews in batches as a
  table.
- Periods are identified by `period_end` (ADR-05), never by the `fiscal_year` /
  `fiscal_period` metadata, which is wrong for quarters (see `state/aberto.md`).

### What was rejected
**Chunk IDs as labels** (`00012_0003`): exact, but every re-chunk silently invalidates
the whole set — and P1 is about to change chunking.

### Tradeoff accepted
An evidence phrase can appear in more than one chunk (overlap of 200 chars), so a
question may have several "relevant" chunks; Recall@k counts any of them.

### Would be false if
Evidence phrases turn out to be too short to be distinctive (e.g. a margin value that
appears in several periods' text) — the four metadata fields exist to prevent that.
Test: report the number of matching chunks per label in `validate.py` (not yet done)
and flag labels that match many chunks.

---

## ADR-16 — Retrieval scored deterministically against the golden set (Recall@k, MRR, nDCG)

**Status:** Active

### Context (2026-10-24)
P0a is done: 80 reviewed questions (ADR-15). P0b must turn them into a retrieval
baseline that every P1 change (BM25, rerank, contextual headers) is compared against.
Sources are cited by id from `docs/REFERENCES.md`.

### What was decided
- **Method: a Cranfield-style test collection** (REF-01, REF-02) — fixed corpus, fixed
  questions, fixed relevance labels — so one component can be changed at a time and
  its effect isolated. This is also the grounding of ADR-15's labels: a chunk is
  relevant if it *contains the evidence*, as in DPR's answer-containment accuracy
  (REF-06) and FinanceBench's evidence strings over filings (REF-07).
- **What runs:** `eval/golden/score.py` imports the production `Retriever`
  (`rag/retrieve.py`) with production settings (auto-detected filters, per-company
  search, ADR-08/09). Locally; never touches the VPS. The 12 `out_of_corpus`
  questions have no expected source and are scored in P0c (refusal), not here.
- **Metrics, per category and overall, at k = 5, 10, 20:**
  - **Recall@k** — share of expected sources found in the top k.
  - **All-sources@k** — every expected source found (matters for comparisons).
  - **MRR** — 1/rank of the first relevant chunk (REF-05).
  - **nDCG@k** — binary relevance.
  This is the metric set of REF-08 (financial text+table retrieval), so our numbers
  can be read against theirs. k = 5 is production; k = 20 follows the industry
  practice of 1 − Recall@20 (REF-09) and shows what a reranker could recover.
- **Uncertainty:** with ~68 scored questions (12–15 per category), small differences
  reverse easily on another sample (REF-03). Every comparison between two
  configurations reports a **paired bootstrap 95% confidence interval** (as REF-08); a
  difference whose interval contains 0 is recorded as "not detectable", never as a gain.
- **Incomplete labels:** a figure can appear in chunks the label does not point to,
  and an unlabelled correct chunk counts as a miss (REF-04). After the baseline run,
  top-k misses are checked for the expected figure/evidence; a label is widened only
  with the owner's approval, recorded in the changelog.
- **Self-check of the scorer:** an oracle run that returns the labelled chunks must
  score 1.0 on every metric; and the number of chunks matching each label is reported
  (the test ADR-15 left pending). Engineering practice, not a literature claim.
- **Cost:** only question embeddings (~68 calls, < $0.001 per run); query vectors are
  cached on disk so P1 runs compare identical queries at no extra cost.
- **Output:** one JSON per run under `eval/results/` (date, git commit, config,
  per-question ranks); the summary table lives in a single document, which the
  roadmap points to.

### What was rejected
**Ragas context recall as the primary retrieval metric** (REF-10): it uses an LLM
judge — paid per run, not deterministic, and dependent on a second model agreeing.
The evidence match is free and repeatable. Ragas stays for generation quality in P0c.

### Tradeoff accepted
Evidence matching undercounts when the same fact is phrased differently in another
chunk (mitigated by the miss review above, not eliminated); and ~68 questions only
detect large effects per category.

### Would be false if
The oracle run scores below 1.0 (the scorer is wrong, not the retriever); or, on the
miss review, a large share of "misses" turn out to contain the expected answer — then
the labels, not the retriever, dominate the score and ADR-15's labelling must be
revised before any P1 comparison.

---

## ADR-17 — The per-company cap is ignored when the filter pins a single company

**Status:** Active

### Context (2026-10-24)
P0b (EV-01, `docs/EVALUATION.md`) showed that the app passes `max_per_company=2`
whenever no company is picked in the sidebar, and that the cap was also applied when
the question itself names one company (auto-detected filter). 56 of 68 golden-set
questions received 1–2 chunks although `top_k=5`. ADR-09 already states the cap's
purpose: balance for "all companies" queries.

### What was decided
In `Retriever.retrieve()`, when the active filter resolves to exactly one company,
`max_per_company` is dropped: the cap can only truncate such a query, never balance it.
Multi-company queries keep per-company retrieval (ADR-09); queries with no company keep
the cap. Fixed at the source, so every caller (app, `eval/evaluate.py`, QA tests)
gets the same behaviour.

### What was rejected
- **Fix in `app.py`** by detecting the company before choosing the cap: duplicates
  `detect_filters`, and `eval/evaluate.py` (same pattern) would stay wrong.
- **Remove the cap altogether:** unfiltered cross-company questions would lose the
  balance ADR-09 describes.

### Measured effect
App configuration before vs after, golden set, k = 5, paired bootstrap (10,000
resamples): Recall@5 **0.338 → 0.518, +0.180 [95% CI +0.099, +0.268]**; figure +0.400,
trend +0.188 detectable. The app now scores identically to the uncapped run. Result
files: `retrieval_2026-10-24T165428Z_app.json` (before), `retrieval_2026-10-24T165929Z_app.json` (after); details in
EV-02.

### Would be false if
A question that names one company needs the cap for answer quality (e.g. answers get
worse with 5 chunks than with 2) — checked in P0c, where generation is scored.

---

## ADR-18 — Golden-set labels are not widened after scoring; undercount accepted

**Status:** Active

### Context (2026-10-24)
ADR-16's miss review found 2 of 45 missed sources at k = 20 (EV-01, EV-02) whose
evidence also exists in a chunk the label does not point to: **nar-02** (same sentence
in NVDA FY2026 10-K §7, label points to §1A) and **cmp-10** (same META sentence in the
2025-09-30 10-Q, label points to the 10-K §7). Crediting them would need an
"alternative sources" field in the golden-set schema (ADR-15).

### What was decided
Labels stay as reviewed. The two cases are recorded as a known undercount, and the
score is reported as a lower bound. The owner's reasoning: the user is not affected
(either chunk gives the analyst the same sentence with a valid citation), so the only
consequence is a lower score — and a score biased low is preferable to one raised by
relabelling after seeing the results.

### What was rejected
**Add alternative sources to the schema and widen the two labels.** Measured gain:
Recall@5 unchanged (0.518); narrative Recall@10 0.533 → 0.600; overall Recall@20
≈ 0.698 → 0.72. Rejected because (1) it changes nothing the user sees; (2) it costs a
schema change in `validate.py`, `score.py` and ADR-15; (3) widening labels *after*
scoring invites inflating the score, the opposite of what the evaluation is for; (4)
P1 comparisons are paired on the same labels, so the undercount hits both arms.

### Tradeoff accepted
Retrieval scores, chiefly at k = 10–20, are slightly pessimistic; a reranker that
promotes the §7 chunk of nar-02 gets no credit for it. Incomplete judgments are a known
property of test collections (REF-04).

### Would be false if
The miss review after any P1 run finds label gaps in **more than 5% of misses**
(today 2/45 ≈ 4%), or a P1 comparison flips sign when those questions are excluded —
then the undercount is no longer negligible and this decision is reopened.

---

## ADR-19 — Fiscal year and quarter from each company's fiscal calendar; dated period headers

**Status:** Active

### Context (2026-10-24)
10-Q labels were derived from the calendar month (`fiscal_year = period_end[:4]`,
Q1 = Jan–Mar), wrong for the three companies whose fiscal year does not end in
December: Apple's quarter ended 2025-12-27 was "FY2025 Q4" (it is FY2026 Q1);
24 of 40 10-Qs were mislabelled (AB-06 a). Because `detect_filters` turns a year in
the question into a `fiscal_year` filter, a question naming the fiscal quarter
**excluded the right chunk before ranking** — 6 of 14 temporal questions scored 0
even at k = 20 (EV-02). The wrong label also reached the user in the citation.

### What was decided
1. **Fiscal calendar per company** (`data_loaders/fiscal.py`): fiscal year = calendar
   year in which it ends; quarter counted from the month after the fiscal year-end
   (AAPL Sep, MSFT Jun, NVDA Jan, GOOGL/META Dec). Still derived from `period_end`,
   never from XBRL `fy`/`fp` (ADR-05). No 10-K label changes.
2. **Meaning of a year in a question** (owner's rule): a year is a **fiscal** year by
   default ("Apple's profit in 2025" = the year in which that profit was generated);
   when the question contains a **date with a month** ("quarter ended September 30,
   2025", "Sept. 2025", "2025-09-30"), its years match the **calendar** year of
   `period_end` (`RetrievalFilters.calendar_year`). The sidebar's explicit "Fiscal Year"
   filter stays strictly fiscal. Year detection extended to 2020–2029 (FY2027 exists).
3. **Dated period headers**: every financial summary states both — "Period: FY2026 Q2
   (quarter ended December 31, 2025)", "FY2025 (fiscal year ended September 27, 2025)".
   A deterministic, metadata-derived form of contextual chunk headers (REF-09, REF-08)
   and of ADR-03's natural-language rendering: the text a calendar-dated question
   embeds against now contains the date.
4. **Applied to the existing corpus without re-ingesting**
   (`stages/migrate_fiscal_labels.py`, idempotent, backup in
   `data/processed/backup_pre_adr19/`): re-ingesting would pull filings published
   since, and the effect could not be attributed. Changed only `fiscal_year` /
   `fiscal_period` and the 40 summary headers; exactly those 40 vectors re-embedded.

### What was rejected
- **Fiscal only, no date exception:** measured — fig-15, tmp-15, tmp-16 (dates copied
  from 10-Q cover pages) fall out entirely (EV-03, intermediate run).
- **Year matches fiscal *or* calendar always:** never excludes the right chunk, but
  "Apple's profit in 2025" would also admit FY2026's December quarter; the owner
  ruled that a bare year means the fiscal year.
- **Detect the word "fiscal":** brittle — "Apple's 2025 revenue" means fiscal without
  saying it.
- **Fiscal label alone in the header** (first version): fig-13 fell from rank 3 to 9
  with the *same* candidate set — the old wrong header "FY2025 Q4" matched "2025" by
  accident; the correct "FY2026 Q2" carried no calendar cue.

### Measured effect (EV-03)
Golden set 70 scored questions, k = 5, paired bootstrap vs before ADR-19: temporal
Recall@5 **0.500 → 0.812** (+0.312, 95% CI +0.125 to +0.562); overall **0.532 →
0.607** (+0.075, CI +0.014 to +0.146); figure stays 1.000 with MRR 0.561 → 0.797; no
category decreases.

### Would be false if
A fiscal-year question on a non-calendar company retrieves a quarter of the adjacent
fiscal year as its top source (the label or the rule is wrong) — or a question with
a month that is *not* a period date (e.g. "Apple's guidance given in May 2025 for
fiscal 2026") is filtered by calendar year and loses the right chunk. The second is a
known edge of the rule; watch for it in P0c answers.

---

## ADR-20 — Versioned releases with "What's new" in the app, from a public CHANGELOG.md

**Status:** Active

### Context (2026-10-24)
The site is a portfolio piece: users and recruiters reach it with no way to see that
it evolves, what changed, or how a change was justified. The owner asked for a
version with an easy "what's new" link.

### What was decided
- **`CHANGELOG.md`** at the repo root, in English, [Keep a Changelog] format,
  Semantic Versioning (minor = improvement users notice, patch = fix, major =
  architecture change). It is the **only place** the version number lives; the app
  parses its newest entry (`latest_release()` in `app.py`). Distinct from
  `state/changelog.md`, which is internal and in Portuguese.
- **Two places in the app:** a `vX.Y.Z · What's new` popover under the title (first
  thing a visitor reads) and a sidebar footer with version, date and links to the
  changelog, the source code and the ADRs.
- **Two layers per entry:** what changed for the user, with the measured number, then
  links to the ADR / EV records for engineers. Numbers state what they measure
  (retrieval, not answer accuracy) and compare the same question set.
- **Release step:** each published image gets a git tag `vX.Y.Z`.
- Retroactive numbering: v1.0.0 = public launch (2026-05-26, untagged — the exact
  commit deployed then is not recorded); v1.1.0 = ADR-17 + ADR-19.

### What was rejected
**GitHub Releases only:** invisible to visitors of the site, which is where the
portfolio is seen. **Version constant in code:** a second place to keep in sync with
the changelog.

### Would be false if
Visitors don't open it (no analytics today — unverifiable for now), or a release
ships without a changelog entry: the app would then show an outdated version.
Guard: the deploy checklist in `state/handoff.md` includes the changelog entry and tag.

---

## ADR-21 — Hybrid retrieval (BM25 + RRF) implemented and measured; production stays dense until rerank; uniform contextual headers rejected

**Status:** Active

### Context (2026-10-24)
P1a of the roadmap: dense-only retrieval is weak on exact terms in financial text
(REF-08). EV-03 showed narrative Recall@5 0.267 and no trend question with all four
years retrieved.

### What was decided
- **BM25** (`rank-bm25==0.2.2`, REF-12) over the same chunks, built on first use;
  tokens keep inner dots and hyphens ("111.18", "10-k", "fy2026"). Pure Python +
  numpy — `bm25s` would add scipy to the VPS image. Cost measured locally: 1.5 s to
  build, ~40 MB, 10 ms per query.
- **Fusion by Reciprocal Rank Fusion**, k = 60 (REF-11), over the whole corpus;
  metadata filters, per-company retrieval (ADR-09) and the cap rule (ADR-17) apply
  after fusion. The score shown in the app stays the cosine similarity, so its
  relevance percentage keeps its meaning.
- `Retriever(mode=...)`: `dense` | `bm25` | `hybrid`; `score.py run --mode`.
- **Production stays `dense`.** The hybrid ranking is kept as the **candidate pool for
  the reranker (P1b)** and ships only together with it, if the pair beats EV-03.
  Owner's decision, on the measured trade-off below.

### Measured (70 scored questions, Recall@5, paired bootstrap vs EV-03 dense)
| | dense | bm25 | hybrid |
|---|---|---|---|
| narrative | 0.267 | **0.600** (+0.333, CI +0.133 to +0.600) | 0.467 (+0.200, CI 0 to +0.400) |
| trend | 0.333 | 0.417 | **0.479** (+0.146, CI +0.021 to +0.271) |
| comparison | 0.542 | 0.408 | 0.625 |
| figure | 1.000 | 0.933 | 0.933 |
| temporal | 0.812 | 0.438 (−0.375, CI −0.688 to −0.062) | 0.688 (−0.125, n.s.) |
| **all** | 0.607 | 0.570 | 0.646 (+0.039, CI −0.054 to +0.129, n.s.) |

At k = 20 the hybrid pool holds the right narrative chunk for 0.867 of questions (dense
0.667) — the gap a reranker is meant to close. Files: `eval/results/retrieval_2026-10-24T1806*`.

### What was rejected
- **Ship hybrid now:** overall gain not detectable, and the loss falls on period
  questions — for an analyst the costliest error (a figure from the wrong quarter
  looks right). REF-08's best result is hybrid **plus** rerank, not hybrid alone.
- **Tune the RRF weights toward dense:** with 70 questions that tunes the system to
  its own test (overfitting).
- **Uniform contextual headers on narrative chunks** ("Apple (AAPL) · 10-K · FY2025
  (fiscal year ended …) · Item 1A Risk Factors" prepended to every chunk, re-embedded,
  ≈ $0.03): dense fell to 0.436 overall (figure 1.000 → 0.600, temporal 0.812 → 0.500);
  only narrative rose (0.533). The header is identical across the hundreds of chunks of
  one filing, so prose chunks start to resemble figure questions and outrank the
  financial summary. Contextual Retrieval (REF-09) writes a context *specific to each
  chunk*; a uniform header does the opposite. (ADR-19's dated header works because
  each summary is a single chunk.) Data and `chunk.py` reverted; dense re-verified
  identical to EV-03.

### Would be false if
Hybrid + rerank (P1b) does not beat EV-03 beyond the confidence interval — then BM25
stays out of production altogether, or the temporal loss persists after rerank.

---

## ADR-22 — Rerank with SubQ Snap over dense candidates; fallback to dense order with a notice

**Status:** Active — deployed in v1.2.0 (2026-10-24)

### Context (2026-10-24)
ADR-14 chose hosted rerankers in a chain, Cloudflare `bge-reranker-base` first
(stable, free daily quota) and SubQ Snap second (faster, preview, finite credits),
on latency and availability — quality had not been measured yet. ADR-21 held the
hybrid retrieval back as the reranker's candidate pool. EV-05 measured both
rerankers over both pools.

### What was decided
- **Production pipeline:** dense retrieval (EV-03) → 40 filtered candidates (20 per
  company in multi-company questions) → **SubQ Snap** scores each passage (P(yes) of a
  "does this passage help answer the question?" decision) → per-company cap → top-k.
  Code: `rag/rerank.py`, `Retriever(reranker=…)`.
- **Chain: SubQ → none.** If SubQ fails or exceeds ~3 s, the answer uses the dense
  order (the best measured ranking without rerank, EV-03) and the page says that
  reranking is unavailable.
- **Cloudflare leaves the chain; BM25 stays out of production** (code kept, ADR-21).
- This revises ADR-14's order: SubQ was second; Cloudflare is dropped.

### Measured (EV-05, 70 scored questions, Recall@5, paired bootstrap vs EV-03)
dense + SubQ **0.607 → 0.811 (+0.204, 95% CI +0.119 to +0.296)**, MRR@5 0.528 → 0.787;
narrative 0.267 → 0.733, comparison 0.542 → 0.733, trend 0.333 → 0.500, temporal
0.812 → 1.000, figure 1.000 → 1.000 — no category decreases. hybrid + SubQ: same
Recall@5, lower MRR (0.733), temporal 0.938. hybrid + Cloudflare: +0.000.

### What was rejected
- **Cloudflare first (ADR-14's order):** measured no gain, so it would serve a
  reranker that changes nothing; as a fallback it lowers temporal and comparison (n.s.)
  — the dense order is the better fallback.
- **Hybrid candidates for SubQ:** no gain over dense, lower MRR, one temporal miss,
  plus BM25's 40 MB and 1.5 s startup (ADR-13: a component must earn its place).

### Risk accepted
SubQ Snap is in preview (intermittent HTTP 403 "model not permitted" on 2026-10-22)
and its credits are finite (≈ 9,000 queries at ~11k tokens each; cost ≈ $0.00045 per
query after credits). The fallback bounds the damage at today's quality (EV-03).
The SubQ key goes to the VPS `.env` through stdin, never printed (same as the OpenAI
key).

### Latency on the VPS (2026-10-24, retrieval only, before answer generation)
1.3–2.0 s for one- or two-company questions; 4.8 s for a five-company comparison,
which makes five sequential SubQ calls (one per company). Parallel per-company calls
are the obvious next step (AB-10).

### Would be false if
On the VPS the SubQ latency or failure rate makes the fallback frequent (watch the
share of answers with the notice), or a larger, fresh question set closes the gap
between SubQ and no rerank.
