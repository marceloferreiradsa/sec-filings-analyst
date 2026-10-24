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

## Input gating and prompt injection

### REF-13 — Not what you've signed up for: Indirect Prompt Injection (Greshake et al.)

**Status:** Verified (arXiv abstract, 2026-10-24)

- **Citation:** K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, M. Fritz.
  arXiv:2302.12173, 2023.
- **Link:** https://arxiv.org/abs/2302.12173
- **Supports:** the distinction between direct injection (typed by the user) and
  indirect injection (planted in data the application retrieves), with a taxonomy of
  impacts. Here the corpus is SEC-only and ingested by the project, so the live risk
  is direct injection and cost abuse.
- **Cited by:** AB-12 (candidate, no decision yet).

### REF-14 — Formalizing and Benchmarking Prompt Injection Attacks and Defenses (Liu et al.)

**Status:** Verified (paper HTML, defenses section, 2026-10-24)

- **Citation:** Y. Liu, Y. Jia, R. Geng, J. Jia, N. Z. Gong. USENIX Security 2024.
  arXiv:2310.12815.
- **Link:** https://arxiv.org/abs/2310.12815
- **Supports:** no existing defense is sufficient on its own. Perplexity filters miss
  almost everything because injected text is fluent. A naive LLM-as-detector has near-zero
  misses but very high false positives (0.83–0.93 on some tasks). Known-answer
  detection was the best detector and still leaks. Implication for an LLM/reranker
  gate: measure false positives on legitimate questions, not just catches.
- **Cited by:** AB-12 (candidate).

### REF-15 — Defending Against Indirect Prompt Injection Attacks With Spotlighting (Hines et al.)

**Status:** Verified (arXiv abstract, 2026-10-24)

- **Citation:** K. Hines, G. Lopez, M. Hall, F. Zarfati, Y. Zunger, E. Kiciman
  (Microsoft). arXiv:2403.14720, 2024 (preprint).
- **Link:** https://arxiv.org/abs/2403.14720
- **Supports:** marking untrusted text so the model can tell data from instructions
  (delimiting, datamarking, encoding) cut attack success from over 50% to under 2% on
  GPT-family models with little task loss. This is the structural layer behind ADR-11's
  grounding prompt. Azure ships it as "Spotlighting" in Prompt Shields:
  https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/content-filter-prompt-shields
- **Cited by:** AB-12 (candidate).

### REF-16 — InjecGuard: Over-defense in Prompt Injection Guardrail Models (Li & Liu)

**Status:** Verified (arXiv abstract, 2026-10-24)

- **Citation:** H. Li, X. Liu. arXiv:2410.22770, 2024 (preprint).
- **Link:** https://arxiv.org/abs/2410.22770
- **Supports:** injection classifiers over-defend. Benign inputs containing trigger
  words ("ignore", "override") are flagged, and state-of-the-art guards fall to about 60%
  accuracy on the NotInject benign set. Any classifier gate needs a false-positive test
  on in-domain questions.
- **Cited by:** AB-12 (candidate).

### REF-17 — An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction (Larson et al.)

**Status:** Verified (arXiv abstract, 2026-10-24)

- **Citation:** S. Larson et al. EMNLP-IJCNLP 2019. arXiv:1909.02027 (CLINC150).
- **Link:** https://arxiv.org/abs/1909.02027
- **Supports:** classifiers that do well on in-scope queries struggle to flag
  out-of-scope ones. This is why an off-topic gate is calibrated on a labelled
  out-of-scope set (here the golden set's `out_of_corpus` questions) rather than on intuition.
- **Cited by:** AB-12 (candidate).

### REF-18 — NeMo Guardrails: Programmable Rails for LLM Applications (Rebedea et al.)

**Status:** Secondary (abstract read; the topical-rail mechanism was not read on the
primary page)

- **Citation:** T. Rebedea, R. Dinu, M. Sreedhar, C. Parisien, J. Cohen. EMNLP 2023
  (demo track). arXiv:2310.10501.
- **Link:** https://arxiv.org/abs/2310.10501
- **Supports:** industry practice of programmable input rails, separate from the
  model, that run before generation, including keeping a bot on topic.
- **Cited by:** AB-12 (candidate).

### REF-19 — LLM Prompt Injection Prevention Cheat Sheet (OWASP)

**Status:** Verified (official page, 2026-10-24)

- **Citation:** OWASP Cheat Sheet Series.
- **Link:** https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- **Supports:** input screening is "not a security boundary": keyword filters miss
  paraphrases, other languages and encodings. It recommends normalising text,
  **limiting input length**, **rate limiting per user/IP**, layered controls, and
  treating retrieved content as untrusted.
- **Cited by:** AB-12 (candidate).

### REF-20 — Llama Prompt Guard 2 model card (Meta)

**Status:** Verified (Hugging Face model card, 2026-10-24)

- **Citation:** Meta, Llama Prompt Guard 2 (86M mDeBERTa-base multilingual; 22M
  DeBERTa-xsmall English-only). Llama 4 Community License, gated repository.
- **Link:** https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M
- **Supports:** a small local classifier option. Reported recall at 1% FPR: 97.5%
  (86M) and 88.7% (22M) in English; latency 92 ms and 19 ms on an A100; 512-token window.
  It flags **only attempts to override instructions**, not off-topic requests.
- **Cited by:** AB-12 (candidate).

### REF-21 — Training a 22MB Prompt Injection Classifier (StackOne)

**Status:** Verified (vendor blog, 2026-10-24); a practitioner report, not peer-reviewed

- **Citation:** H. Dingeto, StackOne engineering blog, May 2026.
- **Link:** https://www.stackone.com/blog/training-22mb-prompt-injection-classifier/
- **Supports:** the argument against an LLM as injection judge (latency, cost,
  privacy, and the judge itself can be injected), and a quantized MiniLM classifier
  (about 23 MB, about 45 ms) as the cheap alternative.
- **Cited by:** AB-12 (candidate).

---
**Última revisão:** 2026-10-24 · detalhe em `state/changelog.md`
