# Aberto

> Pendências vivas. **Escritas no momento em que nascem, riscadas no momento em
> que morrem** — riscar faz parte da regra de roteamento, não é faxina posterior.
>
> **Pendência não é dívida técnica.** Aqui fica a **ação**. A dívida — o que é,
> quanto custa manter, quando vale resolver — é registro canônico em
> `docs/dividas_tecnicas.md`, entra no índice e nunca é removida. Quando há ação
> ativa para pagá-la, a pendência mora aqui e **aponta** para o DT.
>
> Cada uma com detalhe suficiente para retomar **sem** o contexto da sessão que a
> criou. Se precisa da conversa para entender, está mal escrita.
>
> Item resolvido fica com ~~título riscado~~ e uma linha dizendo como foi resolvido.
> Não apagar: saber que algo foi tentado e descartado vale tanto quanto o que ficou.

---

## Adoção do método

> **Esta seção foi escrita pela adoção, não por você.** As pendências dela têm o prefixo
> `AD-` e são transitórias: somem quando a adoção terminar, junto com a seção. A `AD-06`
> é a que faz essa limpeza.
>
> **Agente:** o roteiro completo e as **regras de condução** — uma instrução por vez,
> descobrir em vez de perguntar, não explicar o método — estão no `COMO-ADOTAR.md`. Leia
> antes de conduzir. É a exceção ao "não ler mais nada por padrão", e ela dura só
> enquanto houver `AD-` aberta.

**~~AD-01 — Trazer o produto do projeto para a pasta~~**
O código, o `.pbip`, os notebooks — o que o projeto entrega. A pasta nasce só com o
método, e nada mais faz sentido sem o produto. Se ele já estava aqui, risque.
*resolvida em 2026-10-20: o produto (`app.py`, `pipeline.py`, `stages/`, `rag/`, `eval/`, `tests/`, Docker) já estava na pasta. Alvos do método em `metodo.mk`, incluído no fim do `Makefile`, com os nomes colidentes renomeados (`docs-check`, `docs-index`, `metodo-help`, `metodo-test`, `metodo-clean`) — mesma solução do `constituicao-stf`; ADR a registrar na AD-02, junto com a distribuição de `docs/`.*

**~~AD-02 — Distribuir a documentação existente e indexar~~**
Aponte ao agente onde está o material que você já tem, **sem mover nada antes**. Ele
propõe destino item a item: `docs/` o que você mantém, `refs/` o que outra pessoa
mantém. Nesta fase ele **move e formata; não interpreta conteúdo**. Depois, `make docs-index`.
**Se algo foi para `refs/`:** declare no `refs/_fontes.md` e rode `make intake`.
O `make docs-index` varre `docs/`, não o manifesto — sem isso, `refs/` fica povoado e
não declarado.
*resolvida em 2026-10-20: os 5 documentos ficam em `docs/` (estavam fora do git; entram no commit de adoção). `ARCHITECTURAL_DECISIONS.md`: `## Decision N` → `## ADR-NN` + Status, nome mantido (o README aponta para ele); ADR-12 novo (alvos em `metodo.mk`). `NEXT_FEATURES.md`: `## Feature N` → `## FEAT-NN` + `Status: Proposed`. `ROADMAP_PRIORITIES.md`, `DEPLOYMENT.md`, `EDGAR_TRACK_A_DESIGN.md` sem alteração. `deploy_instructions.txt` segue ignorado; `*.tar.gz` entrou no `.gitignore`. Índice: 0 → 21 registros.*

**~~AD-03 — Preencher "O que é este projeto" no `CLAUDE.md`~~**
Duas ou três frases, mais ambiente e IDs se houver. Credencial nunca. **Riscar as três
primeiras encerra a adoção.**
*resolvida em 2026-10-20: seção preenchida a partir do `README.md` (escopo, portfólio, demo, stack, custo, idioma); nota de adoção removida; convenção dos alvos `docs-*`/`metodo-*` registrada em *Convenções do projeto*.*

**~~AD-04 — Escrever o primeiro handoff real~~**
Ao fim da **primeira sessão de trabalho**, não agora. O handoff que veio com a adoção é
estado de transição; este é o primeiro de verdade, escrito com o que aconteceu na sessão.
*resolvida em 2026-10-21: handoff regenerado do zero ao fim da sessão de análise do roadmap.*

**AD-05 — Ajustar a tabela de roteamento do `CLAUDE.md`**
Ela veio genérica. Ajuste quando souber quais tipos de mudança este projeto realmente
tem — isso se aprende trabalhando, não na adoção.
*aberta desde a adoção*

**AD-06 — Limpar os vestígios da adoção**
Quando `AD-01` a `AD-05` estiverem riscadas: apague a nota de adoção do topo do
`CLAUDE.md`, apague o `COMO-ADOTAR.md` se ainda existir, e apague esta seção inteira.
*aberta desde a adoção*

---

## Decisões de projeto

**~~AB-01 — Decidir se o `docs/ROADMAP_PRIORITIES.md` vira o roadmap do projeto~~**
*resolvida em 2026-10-22: aceito na íntegra — **ADR-13** (roadmap + restrições de VPS e
orçamento + experimento como prova de conceito) e **ADR-14** (rerank via APIs em cascata,
local rejeitado), aprovados pelo titular. FEAT com Status novo (04 e 08 Superseded, demais
Planned com a prioridade); ordem antiga do `NEXT_FEATURES` marcada como superada; roadmap
sem CTO e com §5 "Cost and deploy"; README apontando para o roadmap. O histórico abaixo
fica como registro do caminho.*
Rascunho de 2026-10-20 escrito por outra LLM, com sugestões de aprimoramento: reordena
as features de `docs/NEXT_FEATURES.md` em P0–P4 em torno da pergunta "por que retrieval
se o contexto é enorme?", e **se declara substituto** da *Recommended implementation
order* do `NEXT_FEATURES`. Ninguém aceitou isso ainda — por isso ele ficou em `docs/`
sem alteração e as FEAT-01..09 estão todas como `Proposed`.
Fecha quando o titular decidir: aceito (no todo ou em parte) → ADR com a priorização
escolhida, `Status` das FEAT atualizado e a ordem antiga do `NEXT_FEATURES` marcada como
superada; recusado → registro de por quê, e o documento vai para `arquivo-morto/`.
*aberta desde 2026-10-20*
*Andamento 2026-10-21:* titular **tende a aceitar na íntegra**, condicionado a custo e a
caber na VPS. Já decidido (ainda sem ADR — entra no ADR que fecha esta pendência):
retirar do roadmap toda menção a CTO/liderança (seção 4 vira prova de conceito);
reordenação **local por padrão**, API só se o local for inviável; orçamento de até
~US$20 na OpenAI para o experimento. Proposta minha, a confirmar: ADR-13 com a
priorização + restrição "produção cabe na VPS, imagem sem torch"; seção "Custo e deploy"
no `ROADMAP_PRIORITIES` como lugar único das estimativas de custo (as tabelas desta
sessão estão só na conversa e no README do experimento). Fecha depois da AB-03/AB-04.
*Andamento 2026-10-22:* depois da medição da Cloudflare, o titular **passou a tender à
API**, desde que a cota grátis seja generosa e haja fallback quando ela acabar (no plano
Free a requisição falha com erro, não é cobrada; volta às 00:00 UTC — página de preços
da Cloudflare). Desenho proposto, não decidido: Cloudflare → (opcional: MiniLM local ou
segunda API) → sem reordenação (ordem do BM25 + denso). A camada do meio só entra se o
P0 mostrar que reordenar vale o peso. Pendente para validar a cota: conferir no painel
da Cloudflare quantos neurons as ~64 chamadas de 2026-10-22 consumiram (a página não diz
se a pergunta conta junto com os trechos).
*Decidido 2026-10-22 (sem ADR ainda — entra no ADR da AB-01):* reordenação **via API em
dois níveis** — 1º Cloudflare `bge-reranker-base`, 2º uma segunda API (a escolher, AB-04)
— e 3º **sem reordenação, com aviso explícito na página** quando esse nível responder.
Isso **substitui a decisão de 2026-10-21** ("local por padrão"); o local vira
alternativa rejeitada, com as medições da AB-03 como fundamento.
*Decidido 2026-10-22 (noite):* 2ª API = **SubQ Snap** (`subq-snap-1.1`). Ordem final:
Cloudflare → SubQ → sem reordenação com aviso (ver AB-04). Próximo passo desta pendência:
redigir o ADR (com as decisões 2026-10-21/22), a seção "Custo e deploy" e tirar CTO do
roadmap, atualizar Status das FEAT — **discutir o rascunho antes de escrever**.

**AB-03 — Reordenação local: rodar as alavancas e fechar o veredito**
Resultado na VPS (2026-10-22) e critério em `experiments/rerank_latency/README.md`:
veredito preliminar *viável com concessão* (MiniLM-L6 e jina-tiny < 2,0 s p95 com 20
candidatos, 2 threads). Falta, tudo a custo zero: (a) conferir a rodada local completa
(`results/local-5900x-cpus2_*.json`, rodava ao fechar a sessão); (b) investigar pico de
RSS ~2 GB que cresce com repetições (hipótese: arena do ONNX Runtime); (c) testar int8
quantizado, truncamento a 256 tokens, `batch_size` menor; (d) corrigir `model_disk_mb`
no `bench.py`; (e) reescrever o veredito no README.
*2026-10-22:* com a decisão pela API (AB-01), o local não vai para produção. O escopo
encolhe para **fundamentar a rejeição no ADR**: (a) e (e) são necessários; (b)–(d) só se
o titular quiser o veredito local completo (alavancas poderiam mudar a conclusão — o
ADR deve dizer que não foram testadas, se não forem).
*2026-10-22 (noite):* a rodada local completa de 2026-10-21 **não gravou resultado** (o
container morreu com a sessão). Refazer (a) numa sessão que fique aberta, ou aceitar
só os 3 pontos locais válidos já no README.
*aberta desde 2026-10-21*

**~~AB-04 — Latência das APIs de reordenação (plano B)~~**
*resolvida em 2026-10-22: Cloudflare e SubQ Snap medidas (README do experimento); titular
fixou a ordem — 1º Cloudflare `bge-reranker-base`, 2º SubQ `subq-snap-1.1`, 3º sem
reordenação com aviso na página. Razões: Cloudflare estável (0/120 erros) e cota que renova
todo dia; SubQ ~2× mais rápida, mas em preview (403 intermitente) e com cota finita. A
ordem pode ser revista se o P0 mostrar diferença de qualidade.*
`experiments/rerank_latency/api_bench.py` pronto e validado a seco.
*2026-10-22:* **Cloudflare medida** (VPS: p50 0,66 s / p95 2,88 s com 40 candidatos;
resultados no README do experimento). Chaves da Cloudflare ficam em **variáveis de
ambiente de máquina** do Windows (`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`): a
sessão não as herda; o agente lê via `[Environment]::GetEnvironmentVariable(...,'Machine')`
dentro do comando e passa por `--keys-stdin`, sem imprimir. Falta: (1) conferir no painel
da Cloudflare os neurons consumidos em 2026-10-22 (valida a conta de ~2.900 consultas/dia);
(2) rodada com ~50 repetições para firmar o p95 (grátis); (3) **escolher a 2ª API** do
fallback — candidatas Voyage, ZeroEntropy, Jina, SubQ Snap; medir latência de cada uma
que tiver conta (titular cria) e ler `docs.subq.ai`.
*2026-10-22 (noite):* (1) titular não achou neurons por modelo no painel — fica hipótese,
robusta a erro de 10×; (2) feito com 30 repetições: p95 Cloudflare n=40 = 1,30 s na VPS
(o 2,88 s era ruído); (3) **SubQ Snap medido** (chave `SUBQ_SEC_FILINGS_API_KEY`,
variável de máquina): VPS n=40 p50 0,33 s / p95 0,47 s, cobrança uma vez por chamada
(~US$0,00045/consulta), 3/60 erros 403 intermitentes no local. Resultados no README do
experimento. **Falta: titular decidir a ordem dos níveis** (Cloudflare×SubQ) — ou adiar
para o P0 medir qualidade.
Também: ler `docs.subq.ai` e decidir se o **SubQ Snap** (Subquadratic, titular tem
crédito; 100M tokens grátis, US$0,05/1M entrada, 384K de contexto) entra como
reordenador-LLM, roteador do P2 ou braço de contexto longo do P0.
*aberta desde 2026-10-21*

**AB-05 — Limpar o experimento na VPS**
Ficaram na VPS, de propósito, para rodadas novas da AB-03: imagem `rerank-bench`
(~350 MB), volume `rerank-cache` (~2,5 GB de modelos), `/root/rerank-results/`,
`/root/rerank-run.log`, `/root/api_bench.py`, `/root/sample.json`. Quando a AB-03 e a
AB-04 fecharem: `docker rmi rerank-bench`, `docker volume rm rerank-cache`,
`rm -r /root/rerank-results /root/rerank-run.log /root/api_bench.py /root/sample.json`.
*aberta desde 2026-10-21*

**AB-06 — Achados colaterais a triar** (nenhum investigado; cada um pode virar DT ou
correção)
- README diz "20 assertion tests"; `ASSERTION_CASES` tem 10 (e `make eval` repete o 20).
- README diz imagem ~400 MB; a da VPS tem 1,01 GB (`docker images`, 2026-10-21).
- Um 10-K tem só 106 tokens indexados — provável falha de extração (medido em
  `chunks.json`, agrupando por empresa/form/period_end).
- `Makefile`: `VPS_KEY` aponta para `/c/Users/RDPcolthrane/...`; a chave real está em
  `~/.ssh/hostinger_key`.
- Busca rápida em `rag/guards.py` não achou limite de taxa; demo pública com chave paga.
- Claude Code instalado via npm global (2.1.307); auto-update falhando. Sugerido
  `claude install` (nativo) com todas as sessões fechadas.
*aberta desde 2026-10-21*

## Ação manual

**AB-02 — Migrar os alvos do método quando o framework padronizar o prefixo**
O ADR-12 é exceção local (`docs-check`, `docs-index`, `metodo-*`) e diverge do
`constituicao-stf`. A proposta 14 no `PROPOSTA-TEMPLATE.md` do `_template-claude` pede
prefixo único para todos os alvos do método. Quando a versão sair: trazer o `metodo.mk`
novo, refazer as citações (ou nenhuma, se o pacote já vier com os nomes novos),
marcar o ADR-12 como superado e atualizar *Convenções do projeto*.
*aberta desde 2026-10-20*
