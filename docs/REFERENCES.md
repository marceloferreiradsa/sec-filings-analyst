# References

> **Scope:** this document owns the bibliography behind the project's decisions: what
> each source is, where to find it, what it supports here and which decision cites it.
> ADRs and the roadmap cite a source by its `REF-NN` id instead of repeating the
> citation. Numbers *measured in this project* never live here — they live in the
> document that owns the measurement.
>
> **Status** says how the citation was checked: *Verified* = the claim used here was
> read on the primary page (paper, abstract or official post); *Secondary* = only
> bibliographic data and a secondary summary were read — do not quote figures from it
> without opening the primary source.

---

## Retrieval evaluation — method

### REF-01 — The Philosophy of Information Retrieval Evaluation (Voorhees)

**Status:** Secondary (abstract and bibliographic record, 2026-10-24)

- **Citation:** E. M. Voorhees. *The Philosophy of Information Retrieval Evaluation.*
  CLEF 2001 workshop; Springer LNCS 2406 (2002). DOI 10.1007/3-540-45691-0_34.
- **Link:** https://link.springer.com/doi/10.1007/3-540-45691-0_34
- **Supports:** the Cranfield paradigm — evaluate retrieval against a fixed test
  collection (documents, information needs, relevance judgments), so one system
  component can be changed and its effect isolated, without user studies.
- **Cited by:** ADR-16 (grounds the golden set of ADR-15).

### REF-02 — TREC: continuing IR's tradition of experimentation (Voorhees, CACM)

**Status:** Secondary (bibliographic record and summary, 2026-10-24)

- **Citation:** E. M. Voorhees. Communications of the ACM, 2007.
- **Link:** https://cs.uwaterloo.ca/~brecht/courses/854-Experimental-Performance-Evaluation-2017/readings/trec-cacm-2007.pdf
- **Supports:** the Cranfield method as practised at TREC — abstract the retrieval task
  into documents + information-need statements + relevance judgments.
- **Cited by:** ADR-16.

### REF-03 — The Effect of Topic Set Size on Retrieval Experiment Error (Voorhees & Buckley)

**Status:** Verified (NIST abstract, 2026-10-24)

- **Citation:** E. M. Voorhees, C. Buckley. SIGIR 2002.
- **Link:** https://www.nist.gov/node/707561
- **Supports:** with few questions, the chance that "A beats B" reverses on another
  question set of the same size is larger than expected → small differences on a small
  set are not conclusions. Basis for reporting confidence intervals on our ~68 scored
  questions.
- **Cited by:** ADR-16.

### REF-04 — Retrieval Evaluation with Incomplete Information (Buckley & Voorhees)

**Status:** Verified (abstract, 2026-10-24)

- **Citation:** C. Buckley, E. M. Voorhees. SIGIR 2004, pp. 25–32.
  DOI 10.1145/1008992.1009000.
- **Link:** https://ir.webis.de/anthology/2004.sigirconf_conference-2004.5/
- **Supports:** standard measures lose reliability when relevance judgments are
  incomplete (relevant documents left unlabelled count as misses). Basis for reviewing
  "misses" that may be unlabelled correct chunks.
- **Cited by:** ADR-16.

### REF-05 — The TREC-8 Question Answering Track (Voorhees)

**Status:** Secondary (bibliographic record and NIST slides, 2026-10-24)

- **Citation:** E. M. Voorhees. *The TREC-8 Question Answering Track Report.* TREC 1999.
- **Link:** https://trec.nist.gov/pubs/trec8/papers/qa_report.pdf
- **Supports:** origin of Mean Reciprocal Rank as used for QA — score 1/r for the rank
  r of the first correct answer, 0 if none in the list; gives no credit for further
  correct answers.
- **Cited by:** ADR-16.

---

## Retrieval for QA and RAG

### REF-06 — Dense Passage Retrieval for Open-Domain Question Answering (Karpukhin et al.)

**Status:** Verified (paper landing page, 2026-10-24)

- **Citation:** V. Karpukhin et al. EMNLP 2020.
- **Link:** https://aclanthology.org/2020.emnlp-main.550
- **Supports:** top-k retrieval accuracy where a passage counts as relevant if it
  *contains the answer* — the precedent for labelling by evidence text rather than by
  passage/chunk id.
- **Cited by:** ADR-16 (grounds the labelling of ADR-15).

### REF-07 — FinanceBench: A New Benchmark for Financial Question Answering (Islam et al.)

**Status:** Verified (arXiv abstract, 2026-10-24)

- **Citation:** P. Islam, A. Kannappan, D. Kiela, R. Qian, N. Scherrer, B. Vidgen.
  arXiv 2311.11944 (2023).
- **Link:** https://arxiv.org/abs/2311.11944
- **Supports:** open-book QA over public-company filings where each question carries an
  answer and an *evidence string* — the closest precedent to our golden-set schema.
- **Cited by:** ADR-16 (grounds the labelling of ADR-15).

### REF-08 — From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents (Akarsu et al.)

**Status:** Verified (arXiv abstract, 2026-10-24)

- **Citation:** M. Akarsu, R. K. Karaman, C. Mierbach. arXiv 2604.01733 (2026).
- **Link:** https://arxiv.org/abs/2604.01733
- **Supports:** on financial text+table documents, BM25 beat dense retrieval; hybrid +
  neural rerank was best. Reports Recall@k, MRR, nDCG and Number Match with paired
  bootstrap significance — the metric set we adopt, so our numbers are comparable.
- **Cited by:** ROADMAP_PRIORITIES (evidence table, sources), ADR-16, ADR-19, ADR-21.

### REF-09 — Introducing Contextual Retrieval (Anthropic)

**Status:** Verified (official post, 2026-10-24)

- **Citation:** Anthropic engineering blog, September 2024.
- **Link:** https://www.anthropic.com/news/contextual-retrieval
- **Supports:** industry practice of scoring retrieval as 1 − Recall@20 (top-20
  failure rate); contextual embeddings + contextual BM25 + rerank reduced it in their
  tests. Basis for reporting k = 20 and for P1's contextual headers.
- **Cited by:** ADR-16, ADR-19 (dated period headers as a deterministic contextual header),
  ADR-21 (uniform headers rejected: REF-09's context is chunk-specific).

### REF-10 — Ragas: Automated Evaluation of Retrieval Augmented Generation (Es et al.)

**Status:** Verified (arXiv abstract, 2026-10-24)

- **Citation:** S. Es, J. James, L. Espinosa-Anke, S. Schockaert. arXiv 2309.15217
  (2023; v2 2025).
- **Link:** https://arxiv.org/abs/2309.15217
- **Supports:** component-wise RAG evaluation (retrieval vs generation) with LLM-judged
  metrics. Already used by `make ragas`; rejected as the *primary* retrieval metric in
  ADR-16 (paid, non-deterministic), kept for generation in P0c.
- **Cited by:** ADR-16.

---

## Retrieval methods

### REF-11 — Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods (Cormack et al.)

**Status:** Verified (paper PDF, 2026-10-24)

- **Citation:** G. V. Cormack, C. L. A. Clarke, S. Büttcher. SIGIR 2009, pp. 758–759.
  DOI 10.1145/1571941.1572114.
- **Link:** https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
- **Supports:** fusing rankings by summing 1/(k + rank), k = 60 fixed in the paper's
  pilot; RRF equalled or beat each input system and Condorcet / CombMNZ. Needs no score
  calibration between dense and BM25.
- **Cited by:** ADR-21.

### REF-12 — The Probabilistic Relevance Framework: BM25 and Beyond (Robertson & Zaragoza)

**Status:** Verified (publisher page, 2026-10-24)

- **Citation:** S. Robertson, H. Zaragoza. Foundations and Trends in Information
  Retrieval 3(4), 2009, pp. 333–389. DOI 10.1561/1500000019.
- **Link:** https://nowpublishers.com/article/Details/INR-019
- **Supports:** BM25 as the standard lexical ranking function (term frequency
  saturation, length normalisation).
- **Cited by:** ADR-21.

---
**Última revisão:** 2026-10-24 · detalhe em `state/changelog.md`
