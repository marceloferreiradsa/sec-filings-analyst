# Changelog

What changed in SEC Filings Analyst, release by release. The app shows the latest
entry under "What's new"; the version number lives only here (ADR-20).

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
versions follow [Semantic Versioning](https://semver.org/) — minor = an improvement
users notice, patch = a fix, major = an architecture change.

Numbers are retrieval measurements on the project's own benchmark
([docs/EVALUATION.md](docs/EVALUATION.md)): the share of questions for which the
passage holding the answer reaches the model. Answer accuracy is measured separately.

## [1.2.0] — 2026-10-24

### Added
- A second-stage reranker reads your question together with the 40 best candidate
  passages and picks the most relevant ones before the answer is written.
- If the reranker is unavailable, the answer still comes — ordered by semantic
  similarity, as before — and a note under the answer says so.

### Measured
On 70 benchmark questions, the right passage now reaches the model for **81%** of
questions (was 61%): "why" questions **73%** (was 27%), cross-company comparisons
**73%** (was 54%), time-related questions **100%** (was 81%), single figures 100%.

*Engineering detail:* [ADR-22](docs/ARCHITECTURAL_DECISIONS.md#adr-22--rerank-with-subq-snap-over-dense-candidates-fallback-to-dense-order-with-a-notice),
[EV-05](docs/EVALUATION.md#ev-05--p1b-second-stage-rerank-cloudflare-subq-over-dense-and-hybrid-candidates).
Also measured and not shipped: keyword (BM25) hybrid search ([ADR-21](docs/ARCHITECTURAL_DECISIONS.md#adr-21--hybrid-retrieval-bm25--rrf-implemented-and-measured-production-stays-dense-until-rerank-uniform-contextual-headers-rejected)).

## [1.1.1] — 2026-10-24

### Fixed
- Dollar amounts in answers display correctly. Text between two "$" signs was being
  rendered as a math formula — a smaller green font — and the "$" signs disappeared.

## [1.1.0] — 2026-10-24

### Changed
- Fiscal quarters follow each company's fiscal calendar, in answers and citations:
  Apple's quarter ended December 27, 2025 is now *FY2026 Q1*, not *FY2025 Q4*.
- Ask by fiscal year ("fiscal 2026") or by the date on the filing ("quarter ended
  September 30, 2025") — both find the right quarter.
- Questions about a single company now draw on 5 source passages instead of 2.

### Measured
On the same 68 benchmark questions, the right passage is retrieved for **60%** of
questions (was 34%); time-related questions **79%** (was 21%); single-figure
questions **100%** (was 60%).

*Engineering detail:* [ADR-17](docs/ARCHITECTURAL_DECISIONS.md#adr-17--the-per-company-cap-is-ignored-when-the-filter-pins-a-single-company),
[ADR-19](docs/ARCHITECTURAL_DECISIONS.md#adr-19--fiscal-year-and-quarter-from-each-companys-fiscal-calendar-dated-period-headers),
[EV-03](docs/EVALUATION.md#ev-03--retrieval-after-adr-19-fiscal-calendar-dated-headers).

## [1.0.0] — 2026-05-26

### Added
- Initial public release: grounded Q&A over 10-K and 10-Q filings of Apple, Alphabet,
  Meta, Microsoft and NVIDIA, with inline citations and refusal to speculate beyond
  the filings.
