# Handoff — estado do projeto

> **Primeiro arquivo a ler ao abrir sessão.** Regenerado do zero ao fim de cada dia
> de trabalho, a partir de `changelog.md` e `aberto.md`. Teto ~80 linhas.

**Gerado em:** 2026-10-24 (sábado, fim — P1b medido, não publicado)

---

## Onde estamos

Produto no ar (https://secrag.ainati.com.br). Roadmap adotado (ADR-13); rerank decidido
(ADR-14: Cloudflare → SubQ → sem rerank com aviso).

- **P0a** golden set: **82 perguntas**, todas aprovadas (ADR-15). Rótulos não são
  ampliados depois de medir (ADR-18 — nota baixa > nota inflada).
- **P0b** medidor `eval/golden/score.py` (ADR-16). **Linha de base atual: EV-03**
  em `docs/EVALUATION.md` — os números moram lá. Bibliografia em `docs/REFERENCES.md`
  (REF-01..10); o titular quer decisões amparadas: citar `REF-NN`.
- **Corrigido hoje:** teto por empresa cortava perguntas de uma empresa (ADR-17);
  rótulos fiscais dos 10-Q (ADR-19): calendário fiscal por empresa, ano = fiscal por
  padrão e calendário quando a pergunta tem data com mês, cabeçalho dos resumos com
  data por extenso. Dados migrados sem reingerir (`stages/migrate_fiscal_labels.py`,
  backup em `data/processed/backup_pre_adr19/`).

## Como o titular decide

Pelo ponto de vista do usuário (analista fundamentalista): o que muda para quem
pergunta? Erro silencioso (número errado com cara de certo) é o pior caso.

## Como usar o medidor

`.sec-analysis/Scripts/python.exe eval/golden/score.py run --config app` · `run
--oracle` (deve dar 1,000) · `compare A.json B.json` · `labels`. Exportar
`PYTHONIOENCODING=utf-8` no Git Bash. Embeddings das perguntas em cache.
Scripts com regex/barra/aspas: gravar em arquivo via Write e rodar (regra global em
`~/.claude/CLAUDE.md` — o heredoc corrompe barras e aspas nesta máquina).

## Achados de dados (AB-06) ainda abertos

(b) capex de 10-Q acumulado no ano; (c) caixa GOOGL 2026-03-31 repetido; (e) 10-K
FY2022 e NVDA FY2023 sem seção narrativa; (f) só 20/40 10-Q têm resumo XBRL e 5
resumos de 2025 parecem coluna comparativa.

## Segredos — nunca imprimir

Variáveis de máquina: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`,
`SUBQ_SEC_FILINGS_API_KEY`, `OPENAI_API_KEY`. Ler dentro do comando, passar por stdin.
A chave OpenAI da VPS fica em `/root/sec-analyst/.env` (trocada hoje; `.env.bak` com a
antiga, inválida, a apagar). Varrer vazamentos antes de cada commit.

## Deploy

`make check` não roda neste Windows (caminho do make com espaço): rodar build, run,
`PYTHONIOENCODING=utf-8 python tests/test_deployment.py`, stop. Envio: `docker save |
gzip`, `scp -i ~/.ssh/hostinger_key`, na VPS `docker tag …:latest …:prev`, `docker
load`, `docker compose up -d`; `make test-vps VPS_KEY=~/.ssh/hostinger_key`.
**Toda publicação:** entrada nova no `CHANGELOG.md` (público, inglês — o app mostra a
versão de lá, ADR-20) e tag `vX.Y.Z` no commit publicado. **No ar: v1.1.1** (tag
enviada; VPS com `:prev` = v1.1.0).

## Próximos passos — por prioridade

1. **AB-09 — publicar o P1b (decidido: ADR-22).** Denso + SubQ Snap, cascata
   SubQ → ordem densa com aviso; Recall@5 0,607 → **0,811** (EV-05). Faltam: ligar
   `Reranker(chain=("subq",))` no `app.py`/`qa.py`, aviso "sem rerank" na página
   (`retriever.last_rerank == "none"`), chave SubQ no `.env` da VPS (ler a variável de
   máquina e mandar por stdin via SSH), CHANGELOG v1.2.0, build, testes, deploy,
   latência na VPS (~1 h).
2. **AB-06 restante** — inclui (g): pipeline não reproduz o corpus; fixar versões.
3. **P0c** — geração + braço de contexto longo (pago, ≈ US$2–3/rodada).
4. Candidato: intenção temporal ("último trimestre").

Avulsos: AB-05 (limpar VPS; incluir `.env.bak` e imagens antigas) · AB-03 opcional ·
atualizar Claude Code.

## Pendências abertas — ver `aberto.md`

AB-02 · AB-03 · AB-05 · AB-06 · AB-09 · AD-05 · AD-06.

Discutir antes de codar.
