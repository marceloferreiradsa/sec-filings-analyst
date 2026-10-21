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

**AD-04 — Escrever o primeiro handoff real**
Ao fim da **primeira sessão de trabalho**, não agora. O handoff que veio com a adoção é
estado de transição; este é o primeiro de verdade, escrito com o que aconteceu na sessão.
*aberta desde a adoção*

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

**AB-01 — Decidir se o `docs/ROADMAP_PRIORITIES.md` vira o roadmap do projeto**
Rascunho de 2026-10-20 escrito por outra LLM, com sugestões de aprimoramento: reordena
as features de `docs/NEXT_FEATURES.md` em P0–P4 em torno da pergunta "por que retrieval
se o contexto é enorme?", e **se declara substituto** da *Recommended implementation
order* do `NEXT_FEATURES`. Ninguém aceitou isso ainda — por isso ele ficou em `docs/`
sem alteração e as FEAT-01..09 estão todas como `Proposed`.
Fecha quando o titular decidir: aceito (no todo ou em parte) → ADR com a priorização
escolhida, `Status` das FEAT atualizado e a ordem antiga do `NEXT_FEATURES` marcada como
superada; recusado → registro de por quê, e o documento vai para `arquivo-morto/`.
*aberta desde 2026-10-20*

## Ação manual

**AB-02 — Migrar os alvos do método quando o framework padronizar o prefixo**
O ADR-12 é exceção local (`docs-check`, `docs-index`, `metodo-*`) e diverge do
`constituicao-stf`. A proposta 14 no `PROPOSTA-TEMPLATE.md` do `_template-claude` pede
prefixo único para todos os alvos do método. Quando a versão sair: trazer o `metodo.mk`
novo, refazer as citações (ou nenhuma, se o pacote já vier com os nomes novos),
marcar o ADR-12 como superado e atualizar *Convenções do projeto*.
*aberta desde 2026-10-20*
