# Changelog

> **Append-only.** Uma entrada por alteração, escrita **no momento em que acontece**.
> Nunca reescrever nem reorganizar. Entradas mais recentes no topo.
>
> Este arquivo responde "por que isto está assim?" meses depois. O git mostra o
> que mudou; aqui fica o motivo.

**Formato:**
```
## AAAA-MM-DD — título curto

**Mudança:** o que foi feito e por que.
**Documentos tocados:** arquivo (seção) · arquivo (seção)
**Registros:** ADR-NN criado · pendência NN resolvida
**Pendente:** o que ficou (também vai para aberto.md) — ou "nada"
```

---

## 2026-10-24 — v1.2.0 publicada: rerank SubQ no ar

**Mudança:** titular liberou fazer tudo hoje. `app.py` monta o `Retriever` com
`Reranker(chain=("subq",))` e mostra uma nota sob a resposta quando
`last_rerank == "none"`. CHANGELOG v1.2.0, tag `v1.2.0`. Imagem testada local 20/20
com a chave SubQ passada ao container pelo ambiente; chave SubQ gravada no `.env` da
VPS por stdin (sem exibir; `.env` com OPENAI e SUBQ). Publicada (`:prev` = v1.1.1);
`test-vps` 20/20; HTTP 200. Latência da busca na VPS: 1,3–2,0 s (1–2 empresas), 4,8 s
(5 empresas) → AB-10.
**Documentos tocados:** `app.py` · `CHANGELOG.md` · `docs/ARCHITECTURAL_DECISIONS.md`
(ADR-22 status e latência) · `docs/EVALUATION.md` (EV-05 produção, EV-03 histórico) ·
`state/aberto.md` (AB-09 resolvida, AB-10 aberta) · `state/handoff.md`
**Registros:** AB-09 resolvida · AB-10 aberta
**Pendente:** AB-10

## 2026-10-24 — Configuração do rerank decidida (ADR-22)

**Mudança:** titular aceitou denso + SubQ Snap, cascata SubQ → ordem densa com aviso;
Cloudflare fora; BM25 fora de produção. ADR-22 escrito; ADR-14 marcado como revisado
na ordem dos provedores. Chave SubQ: fica na variável de máquina, vai à VPS por stdin
no deploy (sem `.env` local extra).
**Documentos tocados:** `docs/ARCHITECTURAL_DECISIONS.md` (ADR-22, ADR-14 status,
Quick Reference) · `docs/EVALUATION.md` (EV-05 status) · `state/aberto.md` (AB-09) ·
`state/handoff.md`
**Registros:** ADR-22 criado
**Pendente:** etapas 4–5 no sábado (AB-09)

## 2026-10-24 — P1b etapas 1–3: rerank implementado e medido (EV-05) — decisão no sábado

**Mudança:** titular aprovou o desenho (40 candidatos, 20 por empresa; cascata;
fallback para denso em vez de híbrido, por causa do ADR-21). `rag/rerank.py`
(Cloudflare `bge-reranker-base`, SubQ Snap, só biblioteca padrão, chaves do ambiente,
cache opcional) e integração no `Retriever` (`reranker=`, `_collect`, `last_rerank`,
`rerank_score`). Conferido: sem reranker, dense e hybrid idênticos às rodadas
anteriores; cascata testada com chaves inválidas (CF falha → SubQ; ambas → ordem
densa, idêntica ao denso puro). Medido: **SubQ +0,204 no Recall@5 (0,607 → 0,811)**,
denso ou híbrido; Cloudflare 0,000. BM25 não acrescenta com SubQ. Cota da Cloudflare
medida (≈ 2.900 consultas/dia, confirma ADR-14). Custo: ~170 chamadas SubQ ≈ 1,9M
tokens dos créditos; Cloudflare grátis. Produção intocada (dense, sem rerank).
**Documentos tocados:** `rag/rerank.py` (novo) · `rag/retrieve.py` ·
`eval/golden/score.py` (`--rerank`) · `docs/EVALUATION.md` (EV-05) · `eval/results/`
· `state/aberto.md` (AB-09) · `state/handoff.md`
**Registros:** EV-05 · AB-09 aberta
**Pendente:** decisão do titular sobre a configuração (AB-09); etapas 4–5 no sábado

## 2026-10-24 — v1.1.1 publicada; regra global contra heredoc

**Mudança:** antes de publicar, o "What's new" também tinha dois "$" (a própria nota da
v1.1.1) — escape aplicado ao popover; AppTest confirma. Commit `90c50bc`, tag `v1.1.1`,
imagem 758 MB (inclui `rank-bm25`; produção em modo dense, BM25 não é construído),
teste local 20/20, publicada (`:prev` = v1.1.0), `test-vps` 20/20, HTTP 200. Titular
relatou que o heredoc falha em todos os projetos: diagnóstico pelos 3 erros de hoje —
barras invertidas reduzidas à metade e aspas quebrando o parsing no transporte do
comando (Git Bash no Windows). Criado `~/.claude/CLAUDE.md` (global, fora do repo)
com a regra: script com regex/barra/aspas vai para arquivo via Write e roda com
`python <arquivo>`.
**Documentos tocados:** `state/handoff.md` · `~/.claude/CLAUDE.md` (fora do repo)
**Registros:** nenhum
**Pendente:** titular confirmar visualmente a fonte no site

## 2026-10-24 — Híbrido aguarda o rerank (ADR-21); "$" corrigido no app (v1.1.1)

**Mudança:** titular aceitou não ligar o híbrido antes do rerank (amparo: REF-08 —
melhor = híbrido + rerank; perda em temporal é o erro mais caro para o analista).
ADR-21, EV-04, REF-11 (RRF) e REF-12 (BM25) escritos. Titular reportou trechos da
resposta em fonte verde menor: causa = Streamlit renderiza texto entre dois "$" como
LaTeX (e some com os "$"). `escape_dollars()` no `app.py`: "\$" na resposta e no
histórico, "&#36;" no painel de trechos (HTML). Testado: nenhum "$" sem escape, sem
duplicar escape existente; AppTest sem exceções. Versão pública 1.1.1 (patch).
**Documentos tocados:** `app.py` · `CHANGELOG.md` · `docs/ARCHITECTURAL_DECISIONS.md`
(ADR-21, Quick Reference) · `docs/EVALUATION.md` (EV-04) · `docs/REFERENCES.md`
**Registros:** ADR-21 criado · EV-04 · REF-11, REF-12
**Pendente:** publicar v1.1.1; titular confirmar visualmente a fonte no site

## 2026-10-24 — P1a medido: BM25 e híbrido (RRF) implementados; cabeçalhos rejeitados — decisão do titular pendente

**Mudança:** `rag/retrieve.py` ganhou `mode` = dense | bm25 | hybrid (`rank-bm25==0.2.2`,
RRF k=60); produção segue `dense` até decisão. Refatoração conferida: dense idêntico ao
EV-03 trecho a trecho. `score.py run --mode`. Medido (70 perguntas, R@5): BM25 sozinho
0,570 (narrativa 0,267 → 0,600 detectável; temporal 0,812 → 0,438 detectável);
híbrido 0,646 (+0,039, IC −0,054 a +0,129, não detectável; tendência +0,146
detectável; temporal −0,125 e figure −0,067 não detectáveis). Custo BM25: 1,5 s de
construção, ~40 MB, 10 ms/consulta. **Cabeçalhos de contexto nos trechos narrativos
pioraram tudo menos narrativa** (denso 0,607 → 0,436; figure 1,0 → 0,6): cabeçalho
idêntico em centenas de trechos do mesmo filing faz narrativa competir com o resumo de
números. Revertidos dados (backup) e `chunk.py`; dense volta idêntico ao EV-03;
script de migração removido. Re-embedding custou ~US$0,03. Achado: re-rodar
`chunk.py` hoje gera 6.712 trechos, não 6.396 — pipeline não reproduz o corpus
(AB-06 g).
**Documentos tocados:** `rag/retrieve.py` · `requirements.txt` · `eval/golden/score.py`
· `eval/results/` (7 rodadas) · `state/aberto.md` (AB-06 g)
**Registros:** nenhum ainda (ADR-21 após decisão)
**Pendente:** titular decide se o híbrido vai para produção agora ou só com o rerank

## 2026-10-24 — v1.1.0 publicada e marcada

**Mudança:** o 1º build falhou — `.dockerignore` exclui `*.md`, e comentário na mesma
linha do padrão não é aceito; corrigido com `!CHANGELOG.md` em linha própria
(`83ab4ae`). Tag `v1.1.0` recriada no commit corrigido (não tinha saído da máquina) e
enviada com o push. Imagem testada local 20/20 com o `CHANGELOG.md` dentro; publicada
na VPS (`:prev` = imagem do ADR-19); `test-vps` 20/20, site HTTP 200. Duas armadilhas
viraram convenção no `CLAUDE.md`.
**Documentos tocados:** `.dockerignore` · `CLAUDE.md` (Convenções)
**Registros:** nenhum
**Pendente:** nada

## 2026-10-24 — Versionamento visível no app: v1.1.0 e "What's new" (ADR-20)

**Mudança:** titular pediu versão com link "o que há de novo", fácil para usuários e
recrutadores. `CHANGELOG.md` público (inglês, Keep a Changelog, SemVer) é o único lugar
do número de versão; `app.py` lê a entrada mais nova e mostra um popover
`v1.1.0 · What's new` sob o título e versão + links (changelog, código, ADRs) no pé da
barra lateral. Números do texto recalculados nas mesmas 68 perguntas (34% → 60%;
temporais 21% → 79%; número 60% → 100%) — o "34% → 61%" da proposta comparava
conjuntos diferentes. Verificado com `streamlit.testing.AppTest`: sem exceções, popover
e rodapé presentes. Dockerfile copia o `CHANGELOG.md`. README ganhou seção Changelog.
**Documentos tocados:** `CHANGELOG.md` (novo) · `app.py` · `Dockerfile` · `README.md` ·
`docs/ARCHITECTURAL_DECISIONS.md` (ADR-20, Quick Reference)
**Registros:** ADR-20 criado
**Pendente:** publicar e criar a tag `v1.1.0`

## 2026-10-24 — ADR-19 publicado na VPS

**Mudança:** com autorização explícita do titular (o modo automático tinha bloqueado o
deploy), push `9232e99..62cc8cd` e imagem com o índice migrado enviada à VPS; a imagem
anterior (ADR-17) virou `:prev`. `test-vps` 20/20, site HTTP 200.
**Documentos tocados:** nenhum além deste
**Registros:** nenhum
**Pendente:** nada

## 2026-10-24 — Rótulos fiscais concluídos: cabeçalho com data, ADR-19, EV-03

**Mudança:** titular aprovou o cabeçalho com data por extenso e as perguntas tmp-15/16
(`reviewed: true`; 82/82). `period_label()` em `data_loaders/fiscal.py` usado pelo
gerador de resumos e pela migração (agora reescreve os 40 resumos, 10-K e 10-Q;
idempotente — 2ª rodada muda 0). Contra o backup pré-ADR-19: 40 textos e os mesmos 40
vetores, só a linha "Period". Medido: temporal R@5 0,500 → 0,812, geral 0,532 → 0,607
(IC +0,014 a +0,146), figure de volta a 1,000 (fig-13 da posição 9 para 1); nenhuma
categoria cai. Titular perguntou se o enriquecimento de cabeçalho tem amparo: sim —
REF-09 (Contextual Retrieval) e REF-08 (ganhos consistentes de contextual retrieval);
REFERENCES atualizado.
**Documentos tocados:** `data_loaders/fiscal.py` · `data_loaders/edgar_api.py` ·
`stages/migrate_fiscal_labels.py` · `docs/ARCHITECTURAL_DECISIONS.md` (ADR-19, Quick
Reference) · `docs/EVALUATION.md` (EV-03; EV-02 vira histórico) · `docs/REFERENCES.md`
· `eval/golden/golden_set.jsonl` · `eval/results/` · `state/aberto.md` (AB-06 a)
**Registros:** ADR-19 criado · EV-03 · AB-06 (a) resolvido
**Pendente:** publicar na VPS (índice novo vai na imagem)

## 2026-10-24 — Rótulos fiscais dos 10-Q corrigidos (AB-06 a) — em curso, ADR-19 a escrever

**Mudança:** titular aprovou o desenho e a regra "fiscal por padrão, calendário quando a
pergunta tem data com mês". Feito: `data_loaders/fiscal.py` (calendário fiscal por
empresa; 17 casos conhecidos ok, nenhum 10-K muda, 24/40 10-Q corrigidos) ligado aos
dois carregadores; `stages/migrate_fiscal_labels.py` aplicado aos dados atuais sem
reingerir (só `fiscal_year`/`fiscal_period` mudaram, 12 textos e os mesmos 12 vetores
re-embedados; backup em `data/processed/backup_pre_adr19/`); índice reconstruído;
`detect_filters` ganhou `calendar_year` para datas com mês e anos até 2029. Golden set
+2 perguntas (tmp-15, tmp-16, `reviewed: false`) antes de medir. Medido (70 perguntas):
temporal R@5 0,500 → 0,812 (IC +0,125 a +0,562); figure 1,000 → 0,867 (não
detectável): fig-13 caiu da posição 3 para 9 com o mesmo conjunto de candidatos —
causa: o cabeçalho do resumo perdeu o ano de calendário ("FY2025 Q4" → "FY2026 Q2").
Corrigi também uma afirmação minha: o golden set já tinha perguntas de data de
calendário para empresa não-calendário (fig-13, fig-15), que eu não tinha visto.
**Documentos tocados:** `data_loaders/fiscal.py` (novo) · `data_loaders/edgar_api.py` ·
`data_loaders/document_builder.py` · `stages/migrate_fiscal_labels.py` (novo) ·
`rag/retrieve.py` · `eval/golden/golden_set.jsonl` · `eval/results/` (3 rodadas)
**Registros:** nenhum ainda
**Pendente:** decisão do titular sobre cabeçalho com data por extenso; ADR-19, EV-03,
revisão de tmp-15/16, publicar na VPS (índice novo vai na imagem)

## 2026-10-24 — Rótulos do golden set não são ampliados após medir (ADR-18)

**Mudança:** titular recusou AB-08 (b) depois de analisar do ponto de vista do usuário
(analista fundamentalista): os dois casos (nar-02, cmp-10) entregam a mesma frase com
citação válida, então só a nota cai. Princípio do titular: nota punida indevidamente é
preferível a nota inflada indevidamente. Registrado como subcontagem conhecida, com
gatilho de reabertura (> 5% dos erros). Na mesma análise, apontado que o erro mais grave
para o analista é o trimestre errado sem aviso (AB-06 a) — ordem dos próximos passos
em discussão.
**Documentos tocados:** `docs/ARCHITECTURAL_DECISIONS.md` (ADR-18, Quick Reference) ·
`docs/EVALUATION.md` (EV-01, EV-02) · `state/aberto.md` (AB-08)
**Registros:** ADR-18 criado · AB-08 resolvida
**Pendente:** nada

## 2026-10-24 — Publicado na VPS (ADR-17) e chave OpenAI da VPS trocada

**Mudança:** push `a15773b..1643adf`; imagem reconstruída e testada local (20/20,
etapas do `make check` rodadas uma a uma); enviada à VPS. A imagem anterior ficou como
`sec-filings-analyst:prev` para reverter. O `test-vps` acusou 401 `invalid_api_key`:
a chave OpenAI tinha mudado e o `.env` da VPS guardava a antiga — **a demo respondia
erro a perguntas desde a troca da chave** (data desconhecida). Linha `OPENAI_API_KEY`
de `/root/sec-analyst/.env` substituída pela chave do ambiente local, via stdin, sem
exibir (backup `.env.bak`, permissão 600); container recriado. `test-vps` 20/20.
**Documentos tocados:** `state/aberto.md` (AB-08) · `state/handoff.md`
**Registros:** nenhum
**Pendente:** apagar `/root/sec-analyst/.env.bak` (chave antiga, já inválida) e a
imagem `:prev` quando a nova estiver estável

## 2026-10-24 — Teto por empresa deixa de cortar perguntas de uma empresa (ADR-17)

**Mudança:** titular aprovou corrigir AB-08 (a). Em `Retriever.retrieve()`, quando o
filtro resolve para uma única empresa, `max_per_company` é ignorado (o teto só serve
para equilibrar várias empresas, como já dizia o ADR-09). Corrigido na fonte, não no
`app.py`, para valer também no `eval/evaluate.py`. Medido: Recall@5 do app 0,338 →
0,518 (IC 95% +0,099 a +0,268), idêntico à rodada sem teto; pergunta sem empresa
continua com ≤ 2 trechos por empresa. pytest não está no venv; `tests/` só tem teste de
deploy (Docker), não rodado.
**Documentos tocados:** `rag/retrieve.py` · `docs/ARCHITECTURAL_DECISIONS.md` (ADR-17,
Quick Reference) · `docs/EVALUATION.md` (EV-02; EV-01 vira histórico) ·
`eval/results/retrieval_2026-10-24T165929Z_app.json` · `state/aberto.md` (AB-08)
**Registros:** ADR-17 criado · EV-02 · AB-08 (a) resolvido
**Pendente:** publicar na VPS (a demo pública ainda corta) — ação do titular

## 2026-10-24 — P0b: avaliação de retrieval fundamentada e medida (ADR-16)

**Mudança:** titular pediu fundamentação teórica do desenho; pesquisadas e conferidas 10
fontes (Cranfield/TREC, Voorhees & Buckley sobre tamanho de amostra e julgamento
incompleto, MRR do TREC-8 QA, DPR, FinanceBench, Akarsu et al., Contextual Retrieval,
Ragas). A literatura corrigiu o desenho: +nDCG, +bootstrap pareado com IC 95%, +revisão
de erros por rótulo incompleto. Titular aprovou e dispensou o rascunho. Escrito
`eval/golden/score.py` (run / compare / labels; cache de embeddings em
`data/eval_cache/`). Oráculo = 1,000; 116/119 rótulos casam 1 trecho. Linha de base
medida nas configurações app e plain (68 embeddings, < US$0,001). Achado principal: o
teto `max_per_company=2` do `app.py` deixa 56/68 perguntas com 1–2 trechos.
**Documentos tocados:** `docs/REFERENCES.md` (novo) · `docs/ARCHITECTURAL_DECISIONS.md`
(ADR-16; Quick Reference 15 e 16, que faltava o 15) · `docs/EVALUATION.md` (novo, EV-01)
· `docs/ROADMAP_PRIORITIES.md` (status do P0, ponteiro em Sources) ·
`eval/golden/score.py` · `eval/results/` (3 rodadas) · `state/aberto.md`
**Registros:** ADR-16 criado · REF-01..10 · EV-01 · AB-07 resolvida · AB-08 aberta
**Pendente:** AB-08 (a) teto do app e (b) ampliar 2 rótulos — decisões do titular

## 2026-10-24 — Golden set concluído: lote 4 aprovado (P0a)

**Mudança:** titular aprovou as 14 perguntas `temporal` → `reviewed: true`. Invariantes:
80 linhas, 0 `false`, LF, validador ok. P0a fechado com 80 perguntas em 6 categorias.
**Documentos tocados:** `eval/golden/golden_set.jsonl` · `state/aberto.md` (AB-07)
**Registros:** nenhum (AB-07 segue aberta até o P0b consumir o conjunto)
**Pendente:** P0b — métricas de retrieval

## 2026-10-24 — Golden set: lote 3 aprovado, lote 4 redigido (temporal)

**Mudança:** titular aprovou o lote 3 (24 perguntas → `reviewed: true`; invariantes: 66
linhas, 0 `false`, validador ok). Lote 4: +14 perguntas `temporal`, todas de 10-Q, que
testam o rótulo fiscal errado (AB-06 a): "último trimestre" por empresa, trimestre fiscal
nomeado (Q1 FY2026 da Apple = dez/2025, Q2 FY2026 da Microsoft = dez/2025 etc.), data de
calendário ("three months ended") e 2 trimestres de 2023/24 cuja resposta só existe no
texto do MD&A. Validador: 80/80 com todas as evidências no corpus. Ao redigir, AB-06
ganhou (f) e o item (d) não se confirmou.
**Documentos tocados:** `eval/golden/golden_set.jsonl` · `state/aberto.md` (AB-06, AB-07)
**Registros:** nenhum
**Pendente:** revisão do lote 4 pelo titular (AB-07)

## 2026-10-24 — Golden set: lote 3 redigido (comparison + trend)

**Mudança:** +24 perguntas: 12 de comparação (8 de número entre 2–5 empresas, 4
narrativas com uma evidência por empresa) e 12 de tendência (séries FY2022/23→FY2025/26
dos resumos XBRL dos 10-K). Validador: 66/66 perguntas com todas as evidências no corpus.
Perguntas multivalor ficam com `expected_figure: null` e valores em `notes`.
**Documentos tocados:** `eval/golden/golden_set.jsonl` · `state/aberto.md` (AB-07)
**Registros:** nenhum
**Pendente:** revisão do lote 3; lote 4 (temporal, 14).

---

## 2026-10-23 — Golden set: lote 2 aprovado

**Mudança:** titular aprovou as 27 perguntas do lote 2 sem ajustes; `reviewed: true` em
42/42 (sed com invariante: 42 linhas, 27 trocas, 0 restantes, validador passando).
**Documentos tocados:** `eval/golden/golden_set.jsonl` · `state/aberto.md` (AB-07)
**Registros:** nenhum
**Pendente:** lotes de comparison (12), trend (12), temporal (14).

---

## 2026-10-23 — Golden set: lote 2 redigido (narrative + out_of_corpus)

**Mudança:** +27 perguntas: 15 narrativas (3 por empresa, evidência literal de §7 MD&A,
§1A Riscos e §2 de 10-Q) e 12 de recusa obrigatória (empresa fora, período fora,
previsão, dado de mercado, fora de domínio). Validador: 42/42 evidências encontradas.
Achado: FY2022 e NVDA FY2023 sem narrativa no corpus (AB-06 e).
**Documentos tocados:** `eval/golden/golden_set.jsonl` · `state/aberto.md` (AB-06, AB-07)
**Registros:** nenhum
**Pendente:** revisão do lote 2; lotes de comparison, trend, temporal.

---

## 2026-10-23 — Golden set: lote 1 aprovado

**Mudança:** titular revisou as 15 perguntas de número sem ajustes; `reviewed: true` em
15/15 (sed com invariante: 15 linhas, 15 trocas, validador passando).
**Documentos tocados:** `eval/golden/golden_set.jsonl` · `state/aberto.md` (AB-07)
**Registros:** nenhum
**Pendente:** lotes 2–5 (narrative, comparison, trend, temporal, out_of_corpus).

---

## 2026-10-23 — P0a iniciado: desenho do golden set (ADR-15) e lote 1

**Mudança:** desenho do golden set aprovado pelo titular e registrado no ADR-15 (rótulo =
seção + evidência literal, não chunk ID). Criados `eval/golden/golden_set.jsonl` (lote 1:
15 perguntas de número, valores dos resumos XBRL) e `eval/golden/validate.py` (confere
evidências no corpus e arredondamentos; testado com 3 casos falsos, todos reprovados).
Achados de dados nos 10-Q registrados na AB-06. Titular pôs teto de gasto na OpenAI.
**Por quê:** P0 do roadmap (ADR-13) — sem golden set não há métrica de retrieval.
**Documentos tocados:** `docs/ARCHITECTURAL_DECISIONS.md` (ADR-15) · `eval/golden/*`
(novo) · `state/aberto.md` (AB-06, AB-07)
**Registros:** ADR-15 criado · AB-07 aberta
**Pendente:** revisão do lote 1; lotes 2–5.

---

## 2026-10-22 (noite) — docs/ realmente entra no git

**Mudança:** o `.gitignore` tinha um bloco *Additional documents* que ignorava
`ARCHITECTURAL_DECISIONS.md`, `NEXT_FEATURES.md`, `DEPLOYMENT.md` e
`EDGAR_TRACK_A_DESIGN.md` — por isso o commit de adoção (`a15773b`) levou só
`ROADMAP_PRIORITIES.md` e `_index.md`, ao contrário do que a entrada de 2026-10-20 deste
changelog afirma ("`docs/` … entra agora"). O README público apontava para três desses
arquivos: links quebrados no GitHub. Varredura sem nada sensível (só `127.0.0.1` e
placeholders). Titular decidiu versionar os quatro; `deploy_instructions.txt` segue
ignorado.
**Por quê:** os ADRs são a peça de portfólio do projeto e precisam estar no repositório.
**Documentos tocados:** `.gitignore`
**Registros:** nenhum
**Pendente:** nada.

---

## 2026-10-22 (noite) — ADR-13 e ADR-14; roadmap adotado; Status das FEAT

**Mudança:** escritos o ADR-13 (adoção do roadmap sob as restrições de VPS e orçamento;
experimento como prova de conceito) e o ADR-14 (rerank via Cloudflare → SubQ → sem
rerank com aviso; local e torch rejeitados com as medições), sob o novo título *Roadmap
decisions*, mais 2 linhas na tabela de referência rápida e 1 frase na introdução.
`NEXT_FEATURES`: FEAT-04 e FEAT-08 → Superseded; demais → Planned com a prioridade;
ordem antiga marcada como superada. `ROADMAP_PRIORITIES` P1 aponta para o ADR-14.
`README.md` (Roadmap) aponta para o roadmap novo, em vez das prioridades antigas.
**Por quê:** fechar a AB-01. Rascunho apresentado ao titular, dividido em dois ADRs por
serem decisões distintas, cada uma com alternativa rejeitada; aprovado sem ajustes.
**Documentos tocados:** `docs/ARCHITECTURAL_DECISIONS.md` (intro, Quick Reference,
ADR-13, ADR-14) · `docs/NEXT_FEATURES.md` (Status das FEAT, ordem) ·
`docs/ROADMAP_PRIORITIES.md` (P1) · `README.md` (Roadmap) · `docs/_index.md`
**Registros:** ADR-13 e ADR-14 criados · FEAT-01..09 com Status alterado · AB-01 resolvida
**Pendente:** P0 (próximo trabalho); AB-03, AB-05, AB-06.

---

## 2026-10-22 (noite) — ROADMAP_PRIORITIES: sem CTO, experimento como prova de conceito, seção de custo

**Mudança:** retiradas as 3 menções a CTO/liderança; seção 4 reescrita como "proof of
concept and grounds for each choice" (variantes de retrieval, contexto longo × RAG,
cabeçalhos, gerador, latência na VPS, custo por resposta correta); P1 item 3 passa a
descrever o rerank via APIs em cascata (aponta para o ADR-13, ainda em rascunho); nova
**seção 5 "Cost and deploy"** — lugar único das estimativas de custo (preços oficiais
datados, custo por consulta, orçamento do P0 revisto para ≈ US$2–3 por rodada com Batch,
adequação à VPS); fontes de preço acrescentadas.
**Por quê:** decisões do titular de 2026-10-21 (sem CTO; experimento como prova de
conceito) e regra "um fato, um lugar" para os custos. Titular dispensou discussão prévia.
**Documentos tocados:** `docs/ROADMAP_PRIORITIES.md` (P0, P1, §4, §5, Sources) ·
`docs/_index.md` (regenerado)
**Registros:** nenhum novo · referência a ADR-13 pendente de escrita
**Pendente:** ADR-13 (rascunho com o titular).

---

## 2026-10-22 (noite) — Decisão: 2ª API do fallback = SubQ Snap; ordem fixada

**Mudança:** decisão do titular, sem código: Cloudflare `bge-reranker-base` (1º) → SubQ
`subq-snap-1.1` (2º) → sem reordenação com aviso na página (3º).
**Por quê:** Cloudflare estável (0/120 erros) e com cota diária renovável; SubQ ~2× mais
rápida (p95 0,47 s × 1,30 s na VPS), barata e paga pelo crédito do titular, mas em
preview (403 intermitente) e com cota finita. Revisável se o P0 medir diferença de
qualidade.
**Documentos tocados:** `state/aberto.md` (AB-01, AB-04)
**Registros:** AB-04 resolvida · ADR ainda pendente (AB-01)
**Pendente:** ADR da AB-01 + seção de custo + Status das FEAT.

---

## 2026-10-22 (noite) — SubQ Snap medido como reordenador; cauda da Cloudflare firmada

**Mudança:** `api_bench.py` ganhou o provedor SubQ (Decisions API, uma pergunta sim/não
por trecho numa chamada só). Rodadas de 30 repetições, local e VPS, Cloudflare + SubQ.
VPS n=40: SubQ p50 0,33 s / p95 0,47 s; Cloudflare p50 0,68 s / p95 1,30 s. Medido que a
SubQ cobra o texto uma vez por chamada. 3/60 erros 403 intermitentes da SubQ (local).
Nenhum segredo nos resultados (conferido). Rodada local do `bench.py` de 2026-10-21 não
gravou resultado — o container morreu com a sessão.
**Por quê:** AB-04 — escolher a 2ª API do fallback; titular tem crédito na Subquadratic.
**Documentos tocados:** `experiments/rerank_latency/api_bench.py` ·
`experiments/rerank_latency/README.md` (Second run) · `state/aberto.md` (AB-03, AB-04)
**Registros:** nenhum
**Pendente:** ordem dos níveis (titular); rodada local do `bench.py` (AB-03).

---

## 2026-10-22 — Decisão: reordenação via API em dois níveis + nível sem reordenação

**Mudança:** decisão do titular, sem código: 1º Cloudflare `bge-reranker-base`, 2º uma
segunda API (a escolher), 3º sem reordenação com **aviso explícito na página**.
Substitui a decisão de 2026-10-21 ("reordenação local por padrão").
**Por quê:** pela API, o mesmo bge-base que leva 19 s p50 na VPS responde em 0,66 s p50,
sem peso na VPS; a cota grátis estimada (~2.900 consultas/dia, a confirmar) supera com
folga o tráfego da demo; no plano Free a cota esgotada falha com erro, sem cobrança —
daí o fallback.
**Documentos tocados:** `state/aberto.md` (AB-01, AB-03, AB-04)
**Registros:** nenhum ADR ainda — entra no ADR que fecha a AB-01
**Pendente:** escolher a 2ª API; confirmar cota no painel; ADR da AB-01.

---

## 2026-10-22 — Latência da Cloudflare Workers AI (bge-reranker-base) medida

**Mudança:** titular criou o token da Cloudflare (variáveis de máquina). `api_bench.py`
rodado daqui e da VPS, 15 repetições, 0 erros; token conferido ausente dos resultados.
VPS: p50 0,66 s, p95 2,88 s com 40 candidatos — o mesmo modelo leva 19 s p50 rodando
local na VPS.
**Por quê:** AB-04 — medir o plano B antes de decidir a reordenação.
**Documentos tocados:** `experiments/rerank_latency/README.md` (Fallback) ·
`state/aberto.md` (AB-04, AB-05)
**Registros:** nenhum
**Pendente:** firmar o p95 com mais repetições; Voyage; veredito conjunto local × API.

---

## 2026-10-21 — Análise do roadmap, custos e experimento de latência da reordenação local

**Mudança:** leitura do método, do projeto e do `ROADMAP_PRIORITIES` (AB-01). Premissas
do roadmap conferidas no código: retriever é só denso (sem BM25/rerank/RRF); corpus
6.396 chunks ≈ 1,82M tokens (medido em `data/index/chunks.json`); eval = 5 smoke + 10
asserções, nenhuma métrica de retrieval; chunks sem cabeçalho de contexto; falso que
`sentence-transformers` esteja na imagem de produção (só no dev — torch levaria a
imagem a ~3 GB). Preços oficiais levantados (OpenAI, Gemini, Voyage, Cloudflare,
ZeroEntropy, Jina, Cohere, Pinecone, Subquadratic). Hardware medido: VPS = EPYC 9354P,
2 vCPU, 8 GB; local = Ryzen 5900X, RTX 3080 Ti.
Criado `experiments/rerank_latency/` (`bench.py` local ONNX/fastembed sem torch,
`api_bench.py` para APIs, `Dockerfile`, `README.md` com desenho, critério e resultados).
Rodado na VPS e (parcialmente) local.

**Por quê:** o titular tende a aceitar o roadmap na íntegra, condicionado a custo e a
caber na VPS. Decisões do titular nesta sessão: (1) remover do roadmap toda menção a
CTO/liderança — o experimento é prova de conceito e amparo às escolhas; (2)
**reordenação local por padrão; API só se o local se provar inviável**; (3) critério de
viabilidade aprovado antes da medição (p95 ≤ 1,0 s / ≤ 2,0 s, ver README do
experimento); (4) orçamento OpenAI: US$10 de saldo + até US$10 extras para o
experimento.

**Documentos tocados:** `experiments/rerank_latency/*` (novo) · `.gitignore` (amostra
derivada dos experimentos) · `state/aberto.md` · `state/handoff.md` (primeiro real)

**Registros:** nenhum ADR ainda — as decisões (1)–(4) **não estão em ADR**; entram no ADR
que fecha a AB-01 · AD-04 resolvida · AB-03..AB-06 abertas

**Pendente:** AB-01 · AB-03 (alavancas do rerank local) · AB-04 (latência das APIs) ·
AB-05 (limpeza na VPS) · AB-06 (achados colaterais)

---

## 2026-10-20 — Adoção do método

**Mudança:** a estrutura do `ai-project-framework` (versão `2f39f84`) foi instalada pelo
caso B — `CLAUDE.md`, `METODO.md`, `COMO-ADOTAR.md`, `tools/`, `.template/`, `refs/` e
`.gitattributes`. O `Makefile` do método **não** foi copiado: virou `metodo.mk`, incluído
na última linha do `Makefile` do projeto, com `check`/`index`/`help`/`test`/`clean`
renomeados para `docs-check`/`docs-index`/`metodo-*` e as 36 citações reescritas nas
cópias do método (ADR-12). `.gitignore` completado com as entradas do método e com
`*.tar.gz` (imagem Docker de 237 MB solta na raiz). `docs/` — que nunca tinha sido
commitada — entra agora: decisões viraram ADR-01..11 e features FEAT-01..09, todas com
Status. Índice: 0 → 21 registros.

**Por quê:** RAG muda constantemente de funcionalidade e recebe aprimoramentos o tempo
todo; é uma arquitetura que exige acompanhamento contínuo das decisões, para que caminhos
já descartados não sejam retomados sem fundamentação suficiente.

**Documentos tocados:** todos os do método · `Makefile` (include) · `metodo.mk` (novo) ·
`.gitignore` · `docs/ARCHITECTURAL_DECISIONS.md` (cabeçalhos, Status, ADR-12) ·
`docs/NEXT_FEATURES.md` (cabeçalhos, Status) · `CLAUDE.md` (O que é este projeto;
Convenções; nota de adoção removida) · `state/aberto.md`

**Registros:** ADR-12 criado · AD-01, AD-02, AD-03 resolvidas · AB-01 e AB-02 abertas

**Pendente:** AB-01 (aceitar ou não o `ROADMAP_PRIORITIES`) · AB-02 (migrar alvos quando o
framework padronizar o prefixo) · AD-04 (primeiro handoff real) · AD-05 · AD-06.

---
