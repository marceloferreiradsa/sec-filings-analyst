# Handoff — estado do projeto

> **Primeiro arquivo a ler ao abrir sessão.** Regenerado do zero ao fim de cada dia
> de trabalho, a partir de `changelog.md` e `aberto.md`. Teto ~80 linhas.

**Gerado em:** 2026-10-23 (manhã)

---

## Onde estamos

Produto no ar sem mudanças (https://secrag.ainati.com.br). Roadmap adotado (ADR-13),
rerank decidido (ADR-14: Cloudflare → SubQ → sem rerank com aviso). **Em curso: P0a —
golden set** (AB-07), desenho no **ADR-15**: rótulo = `company · filing_type ·
period_end · section` + evidência literal (não chunk ID); `eval/golden/validate.py`
confere cada evidência no corpus antes da revisão.

**Placar: 42/~80 perguntas, todas revisadas e aprovadas pelo titular**
(`eval/golden/golden_set.jsonl`): figure 15 · narrative 15 · out_of_corpus 12.
Faltam: **comparison 12 · trend 12 · temporal 14**.

## Como o titular revisa

Tabela com pergunta, fonte, evidência resumida e resposta; ele responde só com exceções
("tudo ✓"). Dispensou página de revisão com contexto. **O gabarito vem do texto do
filing, nunca de resposta do RAG** (seria circular) — explicado ao titular, que entendeu.
P0b roda local, importando `rag/retrieve.py`; não toca a VPS.

## Achados de dados (AB-06) — corrigir antes do P0c

- Rótulos `fiscal_year`/`fiscal_period` dos 10-Q seguem o calendário, não o ano fiscal.
- Capex dos 10-Q é acumulado no ano, ao lado de receita trimestral.
- Caixa GOOGL 2026-03-31 repete o FY2025.
- **10-K FY2022 (todas) e NVDA FY2023 sem seção narrativa no corpus** — README promete
  FY2022.
O golden set evita esses campos; a categoria temporal vai expor o primeiro.

## Segredos — nunca imprimir

Variáveis de máquina: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`,
`SUBQ_SEC_FILINGS_API_KEY`, `OPENAI_API_KEY`. Ler dentro do comando, passar por stdin.
Varrer arquivos contra vazamento antes de cada commit. Teto de gasto OpenAI: feito.

## Próximos passos — por prioridade

1. **Lote 3** — comparison 12 + trend 12 (dos resumos XBRL + MD&A; comparison tem uma
   fonte por empresa).
2. **Lote 4** — temporal 14 ("último trimestre", rótulos fiscais por empresa).
3. **P0b** — métricas de retrieval (Recall@k, MRR) no `eval/`, linha de base do denso
   atual; custo < US$0,01.
4. **P1a** — BM25 + RRF + cabeçalhos de contexto. Depois P1b (cascata de rerank).
5. **P0c** — geração + contexto longo (pago, ≈ US$2–3/rodada) — após corrigir AB-06.

Avulsos: AB-05 (limpar VPS) · AB-06 restante · AB-03 opcional · atualizar Claude Code.
Recarga OpenAI: não precisa até o passo 5.

## Pendências abertas — ver `aberto.md`

AB-02 · AB-03 · AB-05 · AB-06 · AB-07 · AD-05 · AD-06.

Discutir antes de codar.
