# Handoff — estado do projeto

> **Primeiro arquivo a ler ao abrir sessão.** Regenerado do zero ao fim de cada dia
> de trabalho, a partir de `changelog.md` e `aberto.md`. Teto ~80 linhas.

**Gerado em:** 2026-10-24 (sábado, fim do dia)

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
Scripts Python longos: gravar em arquivo, não em heredoc (o heredoc já quebrou com
barras invertidas e aspas).

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

## Próximos passos — por prioridade

1. **P1a** — BM25 + RRF + cabeçalhos de contexto; comparar com EV-03 por
   `score.py compare`. Alvos: narrativa (R@5 0,267) e tendência (All@20 = 0).
2. **P1b** — cascata de rerank (ADR-14); folga entre R@5 e R@20 em EV-03.
3. **AB-06 restante** — antes do P0c.
4. **P0c** — geração + braço de contexto longo (pago, ≈ US$2–3/rodada).

Avulsos: AB-05 (limpar VPS; incluir `.env.bak` e imagem `:prev`) · AB-03 opcional ·
atualizar Claude Code.

## Pendências abertas — ver `aberto.md`

AB-02 · AB-03 · AB-05 · AB-06 · AD-05 · AD-06.

Discutir antes de codar.
