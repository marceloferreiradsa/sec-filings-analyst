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

**AD-01 — Trazer o produto do projeto para a pasta**
O código, o `.pbip`, os notebooks — o que o projeto entrega. A pasta nasce só com o
método, e nada mais faz sentido sem o produto. Se ele já estava aqui, risque.
*aberta desde a adoção*

**AD-02 — Distribuir a documentação existente e indexar**
Aponte ao agente onde está o material que você já tem, **sem mover nada antes**. Ele
propõe destino item a item: `docs/` o que você mantém, `refs/` o que outra pessoa
mantém. Nesta fase ele **move e formata; não interpreta conteúdo**. Depois, `make docs-index`.
**Se algo foi para `refs/`:** declare no `refs/_fontes.md` e rode `make intake`.
O `make docs-index` varre `docs/`, não o manifesto — sem isso, `refs/` fica povoado e
não declarado.
*aberta desde a adoção*

**AD-03 — Preencher "O que é este projeto" no `CLAUDE.md`**
Duas ou três frases, mais ambiente e IDs se houver. Credencial nunca. **Riscar as três
primeiras encerra a adoção.**
*aberta desde a adoção*

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

## Categoria (ex.: ação manual · investigação · infraestrutura)

**AB-01 — Título curto e concreto**
O que é, por que importa, e o que precisa acontecer para fechar.
*aberta desde AAAA-MM-DD*
