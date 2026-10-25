# Handoff — estado do projeto

> **Primeiro arquivo a ler ao abrir sessão.** Regenerado do zero ao fim de cada dia
> de trabalho, a partir de `changelog.md` e `aberto.md`. Teto ~80 linhas.

**Gerado em:** 2026-10-24 (sábado, fim — v1.2.0 no ar; próxima sessão: sábado seguinte);
atualização do método em 2026-10-25

---

## Onde estamos

Produto no ar (https://secrag.ainati.com.br), **v1.2.0**: denso + rerank SubQ Snap,
fallback para ordem densa com aviso (ADR-22, revisa a ordem do ADR-14). Roadmap ADR-13.

- **P0a** golden set: **82 perguntas**, todas aprovadas (ADR-15). Rótulos não são
  ampliados depois de medir (ADR-18 — nota baixa > nota inflada).
- **P0b** medidor `eval/golden/score.py` (ADR-16). **Linha de base atual: EV-05**
  em `docs/EVALUATION.md` — os números moram lá. Bibliografia em `docs/REFERENCES.md`
  (REF-01..21); o titular quer decisões amparadas: citar `REF-NN`.
- **Feito em 2026-10-24:** teto por empresa (ADR-17); rótulos fiscais (ADR-19); BM25
  medido e fora (ADR-21); rerank SubQ no ar (ADR-22); "What's new" no app (ADR-20).
- **Método atualizado em 2026-10-25:** comandos do método são `python -m metodo <comando>`
  (pasta `metodo/`); o `Makefile` é só do projeto. ADR-12 superado, AB-02 fechada. `adr`/`dt` recebem o título como argumento.

## Como o titular decide

Pelo ponto de vista do usuário (analista fundamentalista): o que muda para quem
pergunta? Erro silencioso (número errado com cara de certo) é o pior caso. Fonte
sólida (artigo, documentação oficial) antes de decidir; blog sem fonte não ampara.

## Como usar o medidor

`.sec-analysis/Scripts/python.exe eval/golden/score.py run --config app` · `run
--oracle` (deve dar 1,000) · `compare A.json B.json` · `labels`. Exportar
`PYTHONIOENCODING=utf-8` no Git Bash. Embeddings e notas de rerank em cache
(`data/eval_cache/`). Scripts com regex/barra/aspas: gravar em arquivo via Write e
rodar (regra global em `~/.claude/CLAUDE.md`).

## Segredos — nunca imprimir

Variáveis de máquina: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`,
`SUBQ_SEC_FILINGS_API_KEY`, `OPENAI_API_KEY`. Ler dentro do comando, passar por stdin.
Chaves da VPS em `/root/sec-analyst/.env` (OPENAI, SUBQ); `.env.bak` com a OpenAI
antiga, inválida, a apagar (AB-05). Varrer vazamentos antes de cada commit.

## Deploy

`make check` não roda neste Windows: rodar build, run,
`PYTHONIOENCODING=utf-8 python tests/test_deployment.py`, `docker rm -f`. Envio:
`docker save | gzip`, `scp -i ~/.ssh/hostinger_key`, na VPS `docker tag …:latest
…:prev`, `docker load`, `docker compose up -d --force-recreate`; `make test-vps
VPS_KEY=~/.ssh/hostinger_key`. **Toda publicação:** entrada no `CHANGELOG.md`
(público, inglês, ADR-20) e tag `vX.Y.Z`. VPS com `:prev` = v1.1.1.

## Próximos passos — por prioridade

1. **AB-11** — revisar o README contra as mudanças de 2026-10-24 (lista em `aberto.md`).
2. **AB-12** — barrar injeção/fora do escopo antes da geração. Medido: similaridade não
   serve; **P(sim) máxima da SubQ separa** (1,0 vs ≤ 0,05, em 6 perguntas). Proposta
   em camadas: limite de taxa + limite de tamanho da entrada (REF-19) + porteiro SubQ
   calibrado no golden set, **medindo falso positivo** (REF-14, REF-16) + ADR-11.
   Prompt Guard 2 (REF-20) só pega sobrescrita de instrução, não fora do tema.
3. **AB-10** — latência do rerank multiempresa (4,8 s com 5 empresas): SubQ em
   paralelo; `last_rerank` como estado compartilhado.
4. **AB-06 restante** — (b) capex de 10-Q acumulado; (c) caixa GOOGL repetido;
   (e) FY2022 sem narrativa; (f) 20/40 10-Q com resumo; (g) pipeline não reproduz o
   corpus, fixar versões.
5. **P0c** — geração + braço de contexto longo (pago, ≈ US$2–3/rodada).
6. Candidato: intenção temporal ("último trimestre").

Avulsos: AB-05 (limpar VPS: `.env.bak`, imagens antigas) · AB-03 opcional ·
atualizar Claude Code.

## Pendências abertas — ver `aberto.md`

AB-02 · AB-03 · AB-05 · AB-06 · AB-10 · AB-11 · AB-12 · AD-05 · AD-06.

Discutir antes de codar.
