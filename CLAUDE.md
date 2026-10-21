# Instruções do projeto — SEC Filings Analyst

> Lido automaticamente no início de cada sessão. Este arquivo carrega o **método**;
> o **estado** do projeto vive em `state/handoff.md`.

---

## O que é este projeto

**SEC Filings Analyst** é um RAG de perguntas e respostas sobre relatórios 10-K e 10-Q da
SEC de cinco empresas de tecnologia (AAPL, GOOGL, META, MSFT, NVDA; FY2022 – início de
FY2026). Toda resposta é ancorada no texto do filing, com citação inline, e o sistema
recusa especular além dele. É também peça de portfólio para vagas de AI Engineering —
as decisões em `docs/ARCHITECTURAL_DECISIONS.md` são escritas para isso. O entregável é
a aplicação Streamlit em Docker, publicada atrás de nginx.

- **No ar:** https://secrag.ainati.com.br — guia em `docs/DEPLOYMENT.md`
- **Repositório:** `github.com/marceloferreiradsa/sec-filings-analyst` (conta pessoal, HTTPS)
- **Stack:** Python · FAISS · OpenAI Embeddings · GPT-4o-mini · Streamlit
- **Custo:** `make embed`, `make eval`, `make ragas` e perguntas ao RAG fazem **chamada
  paga** à OpenAI (custo estimado na ajuda do `make`). A chave vem de `OPENAI_API_KEY`
  no ambiente — usar, nunca ler nem exibir.
- **Idioma:** código e `docs/` em inglês; método (`CLAUDE.md`, `state/`) em português.

---

## Ao abrir a sessão

1. Ler `state/handoff.md` — onde paramos.
2. Ler `state/aberto.md` — o que ficou pendente.
3. **Não ler mais nada por padrão.** Documentos canônicos são grandes; abrir sob demanda.

---

## Protocolo obrigatório antes de qualquer ação nova

Vale para: investigação, decisão arquitetural nova, verificação de hipótese,
modificação de código, análise.

**Passo 1 — verificar o frescor do índice e consultar.** Antes de buscar, rodar
`make docs-check`. Índice defasado é pior que índice ausente: ele responde, e responde
errado. Se acusar `DEFASADO`, rodar `make docs-index` e só então consultar. A verificação
custa ~25 bytes de saída — ela não é o que consome a janela.

Buscar o tema em `docs/_index.md` por palavras-chave da ação
pretendida. **O índice cobre também a especificação** — manual do cliente,
contrato, RFC — pela lista `EXTRA_SOURCES` do gerador. Documento fora do índice é
documento que ninguém lê no momento certo: é assim que se investiga por semanas algo
que já estava respondido na fonte da verdade.

- Status **resolvido/decidido** → **PARAR.** Citar o registro, reportar que o tema
  está fechado, pedir orientação. Não escrever código nem propor alternativas.
- Status **pendente/em curso** → citar o registro e explicar como a ação nova se relaciona.
- Status **superado** → verificar o que substituiu e citar.

**Passo 2 — se não achou no índice**, fazer grep dirigido nos canônicos. Ler trechos,
nunca o arquivo inteiro.

**Passo 3 — declarar explicitamente** ao iniciar a ação:
> "Antes de propor: verifiquei o frescor do índice e consultei `_index.md` por
> [termos]. [Não encontrei / Encontrei X
> mas não cobre Y]. Sigo com [ação]."

Se essa frase não aparecer, a ação está fora do protocolo e pode ser interrompida.

**Orçamento de investigação.** Antes de investigar, declarar em uma linha o que vou
abrir e por quê: *"Vou olhar A, B e C para decidir X."* Sair dessa lista exige **nova
linha**, não silêncio — é veto barato para o usuário e freio para mim.

Vale para exploração que **procura o que fazer**. Exploração que **alimenta decisão já
tomada** não se corta: ler os corpos antes de reescrevê-los é obrigatório, porque sem
isso o resultado vira transcrição, e transcrição erra.

**Este protocolo existe para evitar refazer trabalho já feito** — o custo de reler o
índice é uma fração do custo de repetir uma investigação.

---

## Regra de roteamento — o que tocar conforme o tipo de mudança

A atualização acontece **na mesma sessão da mudança**. Não existe backlog de documentação.

| Mudei... | Atualizar |
|---|---|
| Código / comportamento | ADR novo se houve escolha com alternativa rejeitada · doc técnico correspondente |
| Estrutura de dados / contrato de interface | doc técnico · ADR novo |
| Resolvi uma dívida técnica | doc de dívidas (status + como) |
| Decisão sem código (escopo, prioridade, conversa) | ADR novo |
| Arquivo entrou ou saiu de `refs/` | `refs/_fontes.md` (manifesto) · `make intake` |
| Registro criado, apagado, renomeado ou com status alterado | `make docs-index` |

**Sempre, ao fim de qualquer alteração:** registrar em `state/changelog.md` (append) e,
se algo ficou por fazer, em `state/aberto.md`.

---

## Um fato, um lugar

Causa conhecida de drift: o mesmo fato escrito a mão em vários documentos.

- **Contagens e percentuais vivem em um único documento.** Os demais apontam.
- **Toda medição carrega data e fonte inline:** `48,9% (medição 06/ago, tabela X)`.
  Sem isso não há como distinguir número corrente de histórico.
- **Toda conclusão carrega o que a falsearia.** Medição é fato; conclusão é
  interpretação, e as duas tendem a ser escritas com o mesmo tom. Ao registrar uma
  conclusão, acrescentar inline *"seria falso se X"*. Escrever o falseador é
  desenhar o teste — e um achado sólido sai reforçado, não bloqueado.
- **O que o usuário vai executar, o agente valida antes.** Célula, query ou script:
  verificar a sintaxe antes de entregar. Se roda num ambiente que o agente não
  alcança, ele é a única barreira.
- Índice guarda **ID, título e status** — o mínimo para achar o registro e decidir
  se pode agir. Nunca contagens nem cópia de conteúdo. E **nunca número de linha**:
  é a única informação que fica falsa em silêncio, porque qualquer edição acima de um
  registro desloca todas as seguintes. O endereço é o próprio ID, procurado com
  `grep` no arquivo que o índice aponta.

---

## Arquivos derivados — o agente escreve, o usuário não

| Arquivo | Como é mantido |
|---|---|
| `docs/_index.md` | Gerado por `make docs-index`. Nunca editado a mão. |
| `state/changelog.md` | Append no momento da mudança. Nunca reescrito. |
| `state/aberto.md` | Pendência escrita quando nasce, riscada quando morre. |
| `state/handoff.md` | Regenerado do zero no fim da sessão. Teto ~80 linhas. |

---

## Economia de contexto

Janela de contexto e crédito são finitos. Portanto:

- **Ler trechos, nunca arquivos inteiros.** O índice dá a linha; ir direto.
- **Editar trechos, nunca reescrever documento completo.**
- Não carregar canônico "por precaução" — abrir quando for de fato usar.
- Preferir consulta direta (SQL, grep, CLI) a montar ambiente pesado para
  responder pergunta simples.
- Se a sessão estiver longa, sugerir fechamento antes da degradação.

---

## Modo de trabalho

- **Discutir antes de codar.** Sempre.
- **Perguntar em caso de dúvida**, não supor. E quando supor for inevitável,
  **marcar explicitamente como hipótese** e registrar como dívida.
- Não escrever código em excesso sem alinhar os passos antes.
- **Verificar antes de afirmar.** Campo existir não significa campo útil: checar
  ausente, presente-mas-zero e presente-mas-órfão são três testes diferentes.
- **Um fio por vez.** Enquanto há decisão do usuário pendente ou execução combinada
  em curso, é o único assunto. Achado colateral vira **uma linha de menção** ao fim
  da resposta, nunca uma sequência de edições.
- **Pertencimento de item.** O critério é **onde o item está registrado**, não qual
  arquivo ele altera. Trabalho de *construir* uma ferramenta vive no `aberto.md`
  dela; trabalho de *usá-la* vive aqui.
- Objetivo: velocidade **com** redução de retrabalho — as duas coisas.

**Esta seção é o espelho versionado das preferências aprendidas.** O que o agente
aprende sobre a pessoa mora fora do repositório e **não é clonado**: quem receber este
projeto recebe um agente sem nada disso. Preferência durável que o time precisa herdar
entra aqui, no mesmo movimento em que vira memória.

**Divergência se resolve medindo, nas duas direções.** Nunca discordar do que o
usuário vê na tela sem medir — e **nunca concordar sem medir**. Concordar sem medir
é o mesmo erro que discordar sem medir, e produz o mesmo retrabalho.

**Observação é ponto de partida; conclusão é interpretação.** O que o usuário
observou — a fórmula, o passo, o número na tela — não se reconfere. O que ele
concluiu a partir disso, sim: ali vale a regra acima.

O custo disso, declarado: aceitar a observação sem reconferir **transfere o peso da
correção para o usuário**. Se o filtro estava errado ou a query não era a que ele
pensava, a investigação inteira parte de um número falso, e eu não vou pegar — porque
foi combinado que eu não pego. Por isso a regra vale **onde eu não alcanço**. Medida
que eu mesmo posso avaliar, query que eu mesmo posso rodar, arquivo que eu mesmo posso
abrir: eu rodo. Aceitar relato ali é preguiça disfarçada de fluidez.

Alternativa que **eu** levantei e precisei descartar para chegar à causa se descarta
**em silêncio** — o relato é da causa encontrada, não do caminho até ela. Alternativa
que **o usuário** levantou tem resposta explícita, sempre: descartar a hipótese dele
calado é ignorá-la.

**Reescrita programática declara invariantes.** Todo script que regrava um arquivo
existente declara antes o que deve ser conservado — contagem de objetos, de comentários
**por estilo**, marcadores de estrutura, codificação e fim de linha — e confere depois
contra `git show HEAD:<arquivo>`. **Contagem que cai é falha até prova em contrário;
contagem que cresce é informação.**

---

## Convenções do projeto

{Padrões de código, nomenclatura, armadilhas conhecidas do ambiente.
Esta seção cresce com o projeto: toda vez que uma armadilha custar tempo,
ela vira uma linha aqui.}

- **Alvos do método têm outro nome aqui** (ADR-12). Os do método estão em `metodo.mk`,
  incluído na última linha do `Makefile`: `make docs-check`, `make docs-index`,
  `make metodo-help`, `make metodo-test`, `make metodo-clean`. Os nomes curtos são do
  projeto: `make check` faz build/run/test do **Docker**, `make index` reconstrói o
  **FAISS** e `make clean` **apaga `data/raw` e `data/processed`**. Instrução de qualquer
  ferramenta do método que diga `make check`/`make index` é texto antigo — usar o nome
  `docs-*`.

---

## Ao fechar a sessão

1. Confirmar que toda mudança do dia passou pela regra de roteamento.
2. Registrar em `state/changelog.md`.
3. Atualizar `state/aberto.md`.
4. Regenerar `state/handoff.md`.
5. Rodar `make docs-index` se algum canônico mudou.
6. Se alguma mudança ficou **sem documentar**, registrar isso em destaque no
   handoff — a próxima sessão começa por aí.
