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
