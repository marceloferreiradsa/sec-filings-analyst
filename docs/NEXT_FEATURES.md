# Next Features

This document captures architectural improvements and new capabilities identified
during the design and build of the SEC Filings RAG system. Each feature is described
with its motivation, implementation path, and estimated effort so they can be
prioritised and built incrementally without disrupting the existing pipeline.

Features are ordered by a combination of impact and implementation simplicity.
Dependencies between features are noted where they exist.

---

## FEAT-01 — Hybrid Retrieval with Structured Data Sidecar

**Status:** Planned — roadmap P3, step 4 only (tool-calling) (ADR-13)

### What it is
A second retrieval path that gives the LLM access to exact raw numeric values
alongside the formatted semantic context it already receives. The current system
renders XBRL numbers as natural language for embedding quality, then discards
the raw values. This feature preserves them in a structured store and makes them
accessible on demand.

### Why it matters
The formatted text maximises semantic retrievability but makes pure arithmetic
inconvenient — the LLM has to parse "$60.92B" back to a number. For queries
like "give me the exact revenue figures for the last four quarters in a format
I can export" or "calculate the compound annual growth rate", raw numbers are
the correct input. This feature removes the tradeoff entirely: semantic search
for meaning, exact lookup for computation.

It also **enables Feature 2 (on-demand charts)** — a chart requires precise
numeric values, not embedded prose.

### How the pointer works
Every embedded chunk already carries the metadata keys needed for a structured
lookup:

```python
chunk.metadata = {
    "company":     "NVDA",
    "period_end":  "2024-01-28",
    "fiscal_year": 2024,
    ...
}
```

A structured store keyed on `(company, period_end)` uses these existing fields
as its lookup index. No new identifiers are needed.

### Implementation path

**Step 1 — Save raw values during ingestion (`edgar_api.py`)**
After building formatted summaries in `build_financial_summaries()`, also write
raw values to `data/processed/xbrl_raw.json`:

```python
# Structure:
{
    "NVDA|2024-01-28": {
        "revenue":          60922000000,
        "gross_profit":     44302000000,
        "operating_income": 32972000000,
        "net_income":       29760000000,
        "rd_expense":       8681000000,
        "capex":            null,
        "cash":             7279000000,
        "long_term_debt":   8462000000
    },
    ...
}
```

No pipeline re-runs required for existing data — the XBRL API calls already
happen; this just preserves an additional output.

**Step 2 — Add structured retrieval to `retrieve.py`**
New method on the `Retriever` class:

```python
def retrieve_structured(
    self,
    company: str,
    period_end: str,
) -> dict | None:
    """Return raw numeric values for a specific company and period."""
    key = f"{company}|{period_end}"
    return self.xbrl_raw.get(key)
```

**Step 3 — Add intent detection and routing to `qa.py`**
Detect whether the question requests exact values and supplement the LLM context:

```python
STRUCTURED_TRIGGERS = [
    "raw numbers", "exact figures", "export", "calculate",
    "compute", "spreadsheet", "precise values", "chart", "plot"
]

def needs_structured_data(question: str) -> bool:
    lower = question.lower()
    return any(t in lower for t in STRUCTURED_TRIGGERS)
```

**Step 4 — Modern implementation: tool-calling (advanced)**
Replace the trigger-keyword detection with OpenAI function/tool calling.
The LLM itself decides mid-generation whether to call `get_raw_financials()`.
This is more robust and requires no keyword maintenance. Implementation
uses the `tools` parameter in `client.chat.completions.create()`.

### Effort
- Steps 1–3: ~3 hours. Small, isolated changes to existing files.
- Step 4 (tool-calling): ~1 additional day. Requires restructuring `qa.py`
  to handle multi-turn tool interactions.

---

## FEAT-02 — On-Demand Chart Generation

**Status:** Planned — after roadmap P3 (ADR-13)

### What it is
When a user asks a question that would be better answered visually — revenue
trends, margin comparisons, quarter-over-quarter growth — the system generates
a Plotly chart and renders it in the Streamlit interface alongside the text answer.

### Why it matters
For the financial analyst use case, charts are often more informative than
prose. "Show me NVIDIA's revenue growth over the last 8 quarters" is answered
better by a bar chart than by a paragraph. This is also a highly visible
portfolio feature — a RAG system that generates charts on demand is
demonstrably more capable than one that only returns text.

### Dependency
**Requires Feature 1.** Charts need precise numeric values, not formatted prose.
The structured sidecar provides the data layer for this feature.

### Implementation path

**Step 1 — Chart intent detection**
Extend the intent detection from Feature 1 to identify chart-specific requests:

```python
CHART_TRIGGERS = [
    "chart", "plot", "graph", "visualise", "visualize",
    "show me", "trend", "compare visually", "over time"
]
```

**Step 2 — Chart builder module (`charts.py`)**
New module that takes structured XBRL data and a chart type and returns
a Plotly figure:

```python
def build_revenue_trend(
    company: str,
    periods: list[dict],   # from structured sidecar
) -> go.Figure:
    ...

def build_margin_comparison(
    companies: list[str],
    metric: str,           # "gross_margin", "operating_margin", etc.
    fiscal_year: int,
) -> go.Figure:
    ...
```

**Step 3 — Streamlit rendering (`app.py`)**
When the answer includes a chart object, render it with `st.plotly_chart()`:

```python
if answer.chart:
    st.plotly_chart(answer.chart, use_container_width=True)
```

### Effort
~1 day after Feature 1 is complete. Plotly is already in the Python ecosystem;
the main work is the chart-type detection logic and the data-to-figure mapping.

---

## FEAT-03 — Section Selection via Configuration File

**Status:** Planned — later, any time (ADR-13)

### What it is
Move the `SECTIONS_TO_INDEX` constant from `html_parser.py` into a
`config.yaml` file. Section selection becomes a configuration change
rather than a code change.

### Why it matters
Currently, adding or removing a section requires opening Python source code.
A config file makes the system usable by non-developers and makes the
decision explicit and visible at the project level. It also makes it trivial
to maintain multiple configurations — a "full corpus" config, a "quick
prototype" config, a "risk-only" config.

### Implementation path

**`config.yaml` (new file in project root)**
```yaml
ingestion:
  sections_to_index:
    10-K: ["1", "1A", "7"]
    10-Q: ["2", "1A"]

  financial_concepts:
    include: ["revenue", "gross_profit", "operating_income",
              "net_income", "rd_expense", "capex", "cash", "long_term_debt"]
```

**`html_parser.py`** — replace the hardcoded constant:
```python
import yaml
config = yaml.safe_load(open("config.yaml"))
SECTIONS_TO_INDEX = config["ingestion"]["sections_to_index"]
```

**`edgar_api.py`** — same pattern for `FINANCIAL_CONCEPTS`.

### Effort
~1 hour. Purely mechanical refactoring, no logic changes.

---

## FEAT-04 — Cross-Encoder Re-ranking

**Status:** Superseded — by ADR-14 (rerank via hosted APIs in a fallback chain; the local cross-encoder below was measured and rejected)

### What it is
After the bi-encoder retriever returns the top-k candidates, a cross-encoder
re-scores them by reading both the query and each chunk together. The final
order is determined by these more precise scores.

### Why it matters
The bi-encoder (text-embedding-3-small) produces one vector per text and
compares them independently — fast but imprecise. A cross-encoder reads the
query and document as a pair and scores their relevance jointly — slower but
significantly more precise. The typical production pattern:

```
Bi-encoder → retrieve top 20 candidates (fast)
Cross-encoder → re-rank to top 5 (precise)
LLM → answer from top 5
```

This is the highest-impact remaining quality improvement in the pipeline.
Benchmarks consistently show 10–20% improvement in retrieval precision over
bi-encoder alone.

### Implementation path

**New dependency** — `pip install sentence-transformers` (already in
requirements.txt) and use a cross-encoder model such as
`cross-encoder/ms-marco-MiniLM-L-6-v2` (runs locally on the 3080Ti).

**`retrieve.py`** — add a `rerank()` method:

```python
from sentence_transformers import CrossEncoder

class Retriever:
    def __init__(self, ...):
        ...
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(
        self,
        question: str,
        candidates: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        pairs = [(question, c.content) for c in candidates]
        scores = self.reranker.predict(pairs)
        ranked = sorted(
            zip(scores, candidates),
            key=lambda x: x[0],
            reverse=True,
        )
        return [c for _, c in ranked[:top_k]]
```

**`qa.py`** — retrieve more candidates, then re-rank before passing to LLM:

```python
candidates = self.retriever.retrieve(question, top_k=20)
final      = self.retriever.rerank(question, candidates, top_k=5)
```

No changes to the index or embeddings. The cross-encoder runs at query time.

### Effort
~2 hours to implement. The cross-encoder model downloads automatically
on first use (~80MB). No pipeline re-runs.

---

## FEAT-05 — User Feedback Loop (Fine-tuning Data Collection)

**Status:** Planned — later; feeds new golden-set questions into P0 (ADR-13)

### What it is
A thumbs-up / thumbs-down button in the Streamlit interface that logs each
question, the retrieved context, and the answer. Over time this accumulates
verified question-answer pairs that can be used to fine-tune either the
embedding model or the LLM.

### Why it matters
As described in the architecture discussions: RAG generates the training data
that improves the model that improves RAG answers. This is the flywheel. A
small UI addition creates a long-term asset.

The logged format is also directly compatible with OpenAI's fine-tuning API,
which expects `{"prompt": ..., "completion": ...}` pairs.

### Implementation path

**`app.py`** — add feedback buttons after each answer:

```python
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("👍 Good answer", key=f"up_{answer_id}"):
        log_feedback(question, context, answer, rating=1)
with col2:
    if st.button("👎 Poor answer", key=f"dn_{answer_id}"):
        log_feedback(question, context, answer, rating=0)
```

**`feedback.py`** (new file) — append to a JSONL log:

```python
def log_feedback(question, context, answer, rating):
    record = {
        "question":  question,
        "context":   context,
        "answer":    answer.answer_text,
        "rating":    rating,
        "model":     answer.model,
        "timestamp": datetime.utcnow().isoformat(),
        "sources":   answer.unique_sources(),
    }
    with open("data/feedback.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")
```

### Effort
~2 hours. Entirely additive — no existing code is modified.

---

## FEAT-06 — Pre-computed Annual Comparison Summaries

**Status:** Planned — roadmap P3 (ADR-13)

### What it is
A single multi-period document per company that consolidates all annual fiscal
year data into one chunk, pre-computing year-over-year growth rates and
describing the margin trajectory. Added to the FAISS index alongside the
existing per-period summaries.

### Why it matters
Currently, answering "how has NVIDIA's revenue grown over four years?" requires
retrieving four separate documents and hoping all four score highly enough to
make it into context. A pre-computed comparison document answers this directly
in a single retrieval.

It also improves answers to calendar year questions. For companies with
non-December fiscal years (NVIDIA ends January, Apple ends September, Microsoft
ends June), the document explicitly notes the fiscal calendar and identifies the
closest fiscal year to any calendar year requested. Instead of a flat refusal,
the system answers: "FY2026 (Feb 2025-Jan 2026) is the closest equivalent to
calendar year 2025, covering approximately 96% of that period."

This is the same principle as Decision 3 in the architecture: pre-compute at
ingestion what users will ask about at retrieval time.

### Implementation path

New function in edgar_api.py called after build_financial_summaries():
takes the already-built per-period summaries, computes YoY growth for each
metric, renders the comparison as a single natural-language document.
No additional API calls required — data is already fetched.

document_builder.py calls the new function and appends the result to the
document list. One additional document per company per form type (10-K and 10-Q).

Metadata: section="annual_comparison", source_type="financial_data",
fiscal_year=None, fiscal_period="MULTI".

### Effort
~2 hours. No new API calls. Requires partial pipeline re-run (ingest.py
forward) to include the new documents in the corpus.

---

## FEAT-07 — Segment-Level XBRL Data (Company Extension Tags)

**Status:** Planned — later (ADR-13)

### What it is
Companies file segment-level financial data using proprietary extension tags
not in the standard US-GAAP taxonomy. Examples: `nvda:DataCenterRevenue`,
`aapl:ServicesRevenue`, `msft:AzureRevenue`. These are currently excluded
from Track A because they live under company-specific namespaces.

### Why it matters
Segment data answers some of the most commercially interesting questions:
"What percentage of NVIDIA's revenue comes from data center?" or "How fast
is Apple's Services segment growing?" These are the questions a trading-oriented
user would ask.

### Implementation path

**`edgar_api.py`** — extend `fetch_company_facts()` to also inspect
company-specific namespaces:

```python
# Current: only reads facts["facts"]["us-gaap"]
# Add: also read facts["facts"][company_namespace]
# where company_namespace is e.g. "nvda", "aapl", "msft"
```

Add a `SEGMENT_CONCEPTS` dict alongside `FINANCIAL_CONCEPTS`:

```python
SEGMENT_CONCEPTS = {
    "NVDA": {
        "data_center_revenue": ["nvda:DataCenterRevenue"],
        "gaming_revenue":      ["nvda:GamingRevenue"],
    },
    "AAPL": {
        "services_revenue":    ["aapl:ServicesRevenue"],
        "iphone_revenue":      ["aapl:IPhoneRevenue"],
    },
    ...
}
```

These tags must be discovered per-company by inspecting their
`companyfacts.json` — there is no standard list.

### Effort
~1 day for discovery (inspecting each company's XBRL namespace) +
~2 hours for implementation. Requires partial pipeline re-run.

---

## FEAT-08 — Query Intent Routing

**Status:** Superseded — absorbed by FEAT-09 9a (ADR-13)

### What it is
A classification step before retrieval that detects whether a question is
asking for structured financial figures or narrative qualitative context,
and automatically applies the appropriate source_type filter.

### Why it matters
"What was NVIDIA's latest revenue?" and "What drove NVIDIA's revenue growth?"
are both about revenue but need different source types. The first needs
financial_data chunks (exact figures from Track A XBRL summaries). The second
needs narrative chunks (MD&A prose explaining the drivers). Without routing,
both queries search the same mixed pool and the wrong chunks can win.

Empirical failure observed: "latest revenue figures for all companies" returned
a 2023 narrative figure for NVIDIA ($18.12B) instead of the FY2026 financial
summary ($215.94B), and returned nothing for MSFT, GOOGL, and AAPL because
their top narrative chunks did not contain explicit revenue figures.

### The two query categories

FIGURE queries — need source_type="financial_data":
- "What was X's revenue/income/margin in [period]?"
- "Latest revenue figures for..."
- "How much did X earn?"
- "Compare margins across companies"

CONTEXT queries — need source_type="narrative":
- "What drove X's revenue growth?"
- "How did X describe its AI strategy?"
- "What risks did X identify?"
- "Explain X's margin expansion"

### Implementation options

Option A — LLM-based router (most robust):
Add a lightweight classification call before retrieval using a cheap model
(gpt-4o-mini, one short prompt, ~100 tokens):

    "Classify this question as FIGURE (needs exact numbers) or CONTEXT
    (needs explanatory text): '{question}'"

Then apply source_type filter accordingly. Cost: ~$0.000015 per query.

Option B — Keyword heuristic (simpler, less robust):
Maintain two keyword sets. If the question matches FIGURE patterns and
does NOT match CONTEXT patterns, apply financial_data filter.

    FIGURE_PATTERNS = ["what was", "how much", "revenue of",
                       "latest figures", "exact", "report"]
    CONTEXT_PATTERNS = ["why", "how did", "what drove", "explain",
                        "describe", "strategy", "risks"]

Option A is recommended — the LLM-based router handles ambiguous cases
correctly and the cost per query is negligible.

### Additional fix: "latest" temporal handling
"Latest" should resolve to the most recent period_end in the corpus
for each company. Add a sort step: when source_type="financial_data"
and no year filter is specified, sort results by period_end descending
and return the most recent entry per company.

### Effort
Option B (keyword heuristic): ~2 hours, retrieve.py + detect_filters()
Option A (LLM router): ~3 hours, new router function in qa.py

---


---

## FEAT-09 — Intelligent Query Understanding

**Status:** Planned — 9a/9b/9f in roadmap P2; 9c/9d later; 9e/9g unscheduled (ADR-13)

### What it is
A pre-retrieval layer that extracts structured intent from free-text questions
and applies filters automatically — so the user never has to know about companies,
fiscal years, source types, or filing formats to get a good answer.

### Why it matters
The current system requires users to think like engineers. They need to know
which sidebar filters to set, what "financial_data" means, that NVIDIA's fiscal
year ends in January. This is wrong for a product. The system should compensate
for vague queries, not require perfectly formed ones.

The shift is from "RAG system that power users operate" to "conversational
assistant that anyone can use."

### Sub-features

**9a — LLM pre-filtering (foundation, implement first)**
One LLM call before retrieval. Extracts company, period, source type, and intent
from natural language:

```
User: "how did nvidia do last year compared to the year before?"

Extracted:
  companies:    ["NVDA"]
  source_type:  "financial_data"
  intent:       "year-over-year comparison"
  periods:      ["most_recent_annual", "previous_annual"]
  filing_type:  "10-K"

→ filters applied automatically
→ annotation shown below answer:
  "Searched: NVDA · 10-K · financial data · FY2024 and FY2023"
```

Cost: ~$0.000015 per query. Eliminates the need for any sidebar interaction
for the majority of queries.

**9b — Query rewriting before embedding**
After extracting intent, rewrite the query before embedding. A casual question
embeds poorly; a precise reformulation embeds much better:

```
Original:   "how did nvidia do last year"
Rewritten:  "NVIDIA annual revenue net income gross margin FY2024"
```

Implemented as a second pass in the pre-filtering LLM call (no extra API call).

**9c — Conversational session context**
Each question is currently independent. A follow-up like "What about Apple?"
has no context to resolve "what about". Appending the last 2–3 exchanges to
the LLM context fixes this. Cost: negligible. Impact: high for multi-turn use.

**9d — Progressive disclosure UI**
Hide the sidebar filters entirely by default. Show only the question input.
Filters accessible via an "Advanced" toggle for power users. The default
experience should be zero-friction.

**9e — Intent disambiguation**
When the query is genuinely ambiguous, present options instead of guessing:

```
"I found NVIDIA data for multiple periods. Which did you mean?
  → FY2024 annual (10-K)
  → Q3 FY2025 quarterly (10-Q)
  → Show all periods"
```

**9f — Natural language date resolution**
"Last quarter" → most recent 10-Q period end.
"Last year" → most recent 10-K.
"2024" → FY2024 with fiscal calendar awareness (NVDA/AAPL fiscal ≠ calendar).

**9g — Graceful failure messages with suggestions**
When the system cannot find relevant context, say why and suggest a reformulation:
"I couldn't find information about Tesla — the corpus covers AAPL, GOOGL,
META, MSFT, NVDA. Did you mean one of these?"

### Implementation order
9a → 9b (same LLM call) → 9d (UI, independent) → 9c → 9f → 9e → 9g

### Effort
9a + 9b: ~4 hours (one new function in qa.py, wires into retrieve.py)
9c:      ~2 hours (session state in app.py)
9d:      ~1 hour (UI restructure in app.py)
9e–9g:   ~1 hour each

---

## Maintenance — pipeline.py status check

`pipeline.py --status` reports `✗ chunk` because it checks
`data/processed/chunks.json` but the authoritative file lives at
`data/index/chunks.json`. One-line fix in `_STATUS_PATHS`:

```python
"chunk": Path("data/index/chunks.json"),   # was: data/processed/chunks.json
```

Effort: 5 minutes.

---

## Summary Table

| # | Feature | Effort | Impact | Depends on |
|---|---------|--------|--------|------------|
| 1 | Hybrid retrieval / structured sidecar | 3h–1d | High | — |
| 2 | On-demand chart generation | 1d | High (visual) | Feature 1 |
| 3 | Config file for section selection | 1h | Medium | — |
| 4 | Cross-encoder re-ranking | 2h | High (quality) | — |
| 5 | Feedback loop / fine-tuning data | 2h | Strategic | — |
| 6 | Annual comparison summaries | 2h | High (trend queries) | — |
| 7 | Segment-level XBRL data | 1–2d | Medium | — |
| 8 | Query intent routing | 2–3h | High (correctness) | — |
| 9 | Intelligent query understanding | 4h–1d | High (UX) | — |
| — | pipeline.py status path fix | 5 min | Maintenance | — |

> **Superseded on 2026-10-22 by ADR-13.** The order below is kept for history; the
> current order is `docs/ROADMAP_PRIORITIES.md` (P0–P4).

**Recommended implementation order (superseded):**
Feature 3 (quick win, maintainability) →
Feature 9a + 9b (highest UX impact, removes user friction) →
Feature 4 (best quality improvement, no pipeline changes) →
Feature 8 (overlaps with 9a, consolidate or skip) →
Feature 9c + 9d (session context + UI cleanup) →
Feature 5 (small UI addition, strategic value) →
Feature 1 → Feature 2 →
Feature 7 (largest effort, most specialised)

**Note on Feature 8 vs Feature 9:**
Feature 8 (query intent routing) overlaps significantly with Feature 9a
(LLM pre-filtering). Both classify query intent before retrieval. Implementing
9a first subsumes Feature 8 — the LLM pre-filter handles source type routing
more robustly than the keyword heuristic in Feature 8. Build 9a and skip 8.
