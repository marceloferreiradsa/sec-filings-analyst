# Índice dos documentos canônicos

> **Arquivo derivado — nunca editar a mão.** Gerado por `make docs-index`
> (`tools/gen_index.py`), varrendo os cabeçalhos de `docs/`.
>
> **Para que serve:** permitir leitura dirigida. Ache o registro aqui pelo
> título ou pelo status, e leia só o trecho — em vez de carregar o documento
> inteiro. Para chegar ao registro, procure o ID no arquivo indicado, com
> `grep -n` pelo cabeçalho.
>
> **Não há número de linha aqui, de propósito.** Era a única informação capaz
> de ficar falsa em silêncio, porque qualquer edição acima de um registro
> desloca todos os seguintes. O ID é o endereço, e ele não se desloca.
>
> **Cobre a especificação, não só a documentação própria.** Manual do cliente,
> contrato ou RFC entram aqui pela lista EXTRA_SOURCES do gerador. Documento de
> fora do índice é documento que ninguém lê no momento certo.

---

## `docs/ARCHITECTURAL_DECISIONS.md`

| ID | Título | Status |
|---|---|---|
| ADR-01 | Two-track ingestion (XBRL + HTML) | Active |
| ADR-02 | Section selection for indexing | Active |
| ADR-03 | Natural-language rendering of XBRL numbers | Active |
| ADR-04 | ASC 606 combine strategy for revenue tags | Active |
| ADR-05 | period_end over the fy field for period identification | Active |
| ADR-06 | frame field as deduplication preference | Active |
| ADR-07 | IndexFlatIP over approximate indexes (IVF, HNSW) | Active |
| ADR-08 | Post-filter with amplification over FAISS IDSelector | Active |
| ADR-09 | Per-company retrieval for multi-company queries | Active |
| ADR-10 | Temperature=0 for the generator | Active |
| ADR-11 | Grounding prompt design | Active |
| ADR-12 | Continuity-method make targets live in `metodo.mk`, with colliding names renamed | Active |
| ADR-13 | Adopt the evidence-driven roadmap, under VPS and budget constraints | Active |
| ADR-14 | Rerank through hosted APIs in a fallback chain; local cross-encoders rejected | Active |
| ADR-15 | Golden set labelled by section + literal evidence, not chunk IDs | Active |


## `docs/NEXT_FEATURES.md`

| ID | Título | Status |
|---|---|---|
| FEAT-01 | Hybrid Retrieval with Structured Data Sidecar | Planned — roadmap P3, step 4 only (tool-calling) |
| FEAT-02 | On-Demand Chart Generation | Planned — after roadmap P3 (ADR-13) |
| FEAT-03 | Section Selection via Configuration File | Planned — later, any time (ADR-13) |
| FEAT-04 | Cross-Encoder Re-ranking | Superseded — by ADR-14 (rerank via hosted APIs i |
| FEAT-05 | User Feedback Loop (Fine-tuning Data Collection) | Planned — later; feeds new golden-set questions  |
| FEAT-06 | Pre-computed Annual Comparison Summaries | Planned — roadmap P3 (ADR-13) |
| FEAT-07 | Segment-Level XBRL Data (Company Extension Tags) | Planned — later (ADR-13) |
| FEAT-08 | Query Intent Routing | Superseded — absorbed by FEAT-09 9a (ADR-13) |
| FEAT-09 | Intelligent Query Understanding | Planned — 9a/9b/9f in roadmap P2; 9c/9d later; 9 |
| Maintenance | pipeline.py status check |  |


## `docs/ROADMAP_PRIORITIES.md`

| ID | Título |
|---|---|
| P0 | Retrieval-level evaluation + long-context baseline *(new, ~1–1.5 days)* |
| P1 | Hybrid retrieval: BM25 + dense + rerank *(Feature 4 + new BM25 path, ~1 day)* |
| P2 | Query understanding *(Feature 9a + 9b + 9f; skip Feature 8, ~4–6h)* |
| P3 | Structured data as a tool *(Feature 1, go straight to step 4; + Feature 6, ~1.5 days)* |
| P4 | "Retrieve, then read" with a larger context *(new, ~0.5–1 day, experimental)* |


---

*30 registros em 3 documentos.*
