# Handoff — estado do projeto

> **Primeiro arquivo a ler ao abrir sessão.** Regenerado do zero ao fim de cada dia
> de trabalho, a partir de `changelog.md` e `aberto.md`. Teto ~80 linhas.

**Gerado em:** 2026-10-24 (sábado)

---

## Onde estamos

Produto no ar sem mudanças (https://secrag.ainati.com.br). Roadmap adotado (ADR-13),
rerank decidido (ADR-14: Cloudflare → SubQ → sem rerank com aviso).

- **P0a concluído:** golden set de 80 perguntas, todas aprovadas pelo titular
  (`eval/golden/golden_set.jsonl`, ADR-15).
- **P0b feito:** `eval/golden/score.py` mede o retriever de produção contra o golden
  set (ADR-16). Linha de base em **`docs/EVALUATION.md` (EV-01)** — os números moram lá.
- **Bibliografia** do método em `docs/REFERENCES.md` (REF-01..10), indexada. O titular
  pediu decisões fundamentadas em literatura/prática de mercado: citar `REF-NN`.

## Achado principal do P0b — decisão do titular (AB-08)

- (a) O `app.py` passa `max_per_company=2` sempre que a barra lateral não tem empresa;
  isso vale também para pergunta de uma empresa só → 56/68 perguntas recebem 1–2
  trechos em vez de 5. Sem o teto, Recall@5 sobe (IC 95% em EV-01). Correção de 1
  linha, mas muda a demo pública. **Não corrigido — aguarda decisão.**
- (b) Ampliar 2 rótulos (nar-02, cmp-10) exige campo de alternativas no schema.

## Como usar o medidor

`python eval/golden/score.py run --config app|plain` · `run --oracle` (autoteste,
deve dar 1,000) · `compare A.json B.json` (bootstrap pareado) · `labels`.
Usar o Python do venv `.sec-analysis/Scripts/python.exe`. Embeddings das perguntas em
cache (`data/eval_cache/`): rodadas novas custam ~0.

## Achados de dados (AB-06) — corrigir antes do P0c

Rótulos fiscais dos 10-Q seguem o calendário (a); capex de 10-Q acumulado (b); caixa
GOOGL 2026-03-31 repetido (c); 10-K FY2022 e NVDA FY2023 sem seção narrativa (e); só
20/40 10-Q têm resumo XBRL e 5 resumos de 2025 parecem coluna comparativa (f).
(d) não se confirmou.

## Segredos — nunca imprimir

Variáveis de máquina: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`,
`SUBQ_SEC_FILINGS_API_KEY`, `OPENAI_API_KEY`. Ler dentro do comando, passar por stdin.
Varrer arquivos contra vazamento antes de cada commit. Teto de gasto OpenAI: feito.

## Próximos passos — por prioridade

1. **AB-08 (a)** — titular decide o teto por empresa; se corrigir, DT/ADR + nova
   rodada `app` + `compare`.
2. **P1a** — BM25 + RRF + cabeçalhos de contexto; medir com `score.py compare`
   (meta: narrativa e temporal, que EV-01 mostra fracas).
3. **P1b** — cascata de rerank (ADR-14); medir R@5 vs R@20 (EV-01 mostra a folga).
4. **Corrigir AB-06** (rótulos fiscais primeiro) — antes do P0c.
5. **P0c** — geração + braço de contexto longo (pago, ≈ US$2–3/rodada).

Avulsos: AB-05 (limpar VPS) · AB-03 opcional · atualizar Claude Code.
Recarga OpenAI: não precisa até o passo 5.

## Pendências abertas — ver `aberto.md`

AB-02 · AB-03 · AB-05 · AB-06 · AB-08 · AD-05 · AD-06.

Discutir antes de codar.
