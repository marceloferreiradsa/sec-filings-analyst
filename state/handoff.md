# Handoff — estado do projeto

> **Primeiro arquivo a ler ao abrir sessão.** Regenerado do zero ao fim de cada dia
> de trabalho, a partir de `changelog.md` e `aberto.md`. Teto ~80 linhas.

**Gerado em:** 2026-10-22 (noite)

---

## Onde estamos

Produto no ar sem mudanças (https://secrag.ainati.com.br). **O roadmap está adotado**:
ADR-13 (ordem P0→P4 de `docs/ROADMAP_PRIORITIES.md`, produção cabe na VPS sem torch,
orçamento OpenAI até ~US$20, experimento como prova de conceito) e ADR-14 (rerank via
Cloudflare `bge-reranker-base` → SubQ `subq-snap-1.1` → sem rerank com aviso na página;
local rejeitado com medições). Custos: só na §5 do roadmap. Latências:
`experiments/rerank_latency/README.md`. Status das FEAT atualizados.

`docs/*.md` passou a ser versionado (estava no `.gitignore` sem ninguém saber; os links
do README estavam quebrados no GitHub).

## Segredos — nunca imprimir

Variáveis de **máquina** do Windows: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`,
`SUBQ_SEC_FILINGS_API_KEY` (e `OPENAI_API_KEY`). Sessão nova herda; senão ler com
`[Environment]::GetEnvironmentVariable(...,'Machine')` dentro do comando e passar por
stdin (`api_bench.py --keys-stdin`). Conferir resultados contra vazamento antes de commit.

## Próximos passos — por prioridade

1. **Teto de gasto na OpenAI** (titular, painel, 5 min) — protege o saldo da demo.
2. **P0a — golden set** (~80 perguntas, 6 categorias, com fontes esperadas). Agente
   redige a partir do corpus (US$0); titular revisa — a parte mais lenta e o ativo
   central.
3. **P0b — métricas de retrieval** (Recall@k, MRR, nDCG) no `eval/`; linha de base do
   denso atual. US$0 (só embeddings das perguntas).
4. **P1a — BM25 + RRF + cabeçalhos de contexto** (re-embed ≈ US$0,04), medido com o P0b.
5. **P1b — cascata de rerank + aviso + log do nível**; medir; antes do deploy: limite
   de taxa no app (AB-06) e segredos na VPS.
6. **P0c — métricas de geração + braço de contexto longo** — a parte paga (≈ US$2–3
   por rodada). Fica depois do P1 para não pagar rodadas repetidas.
7. P2 → P3 → P4, conforme o roadmap.

Avulsos, a qualquer momento: **AB-05** limpar a VPS (5 min) · **AB-06** achados
colaterais · **AB-03** opcional (rodada local completa morreu com a sessão) · atualizar
o Claude Code (`claude install`).

## Saldo OpenAI

Nestes dois dias o gasto OpenAI foi **US$0** (tudo foi local, Cloudflare ou SubQ).
Passos 2–5 ≈ US$0,05. O primeiro gasto relevante é o passo 6. Recarga só ao chegar
nele, depois de medir o custo real de uma rodada.

## Pendências abertas — ver `aberto.md`

AB-02 · AB-03 · AB-05 · AB-06 · AD-05 · AD-06.

Discutir antes de codar.
