# Como adotar — passo a passo

Este documento é o **dono do procedimento**. Se um comando aparece em outro lugar do
repositório, é engano — avise. O `README.md` explica o que o método é; o `metodo/METODO.md`,
por que cada peça existe; aqui está o que fazer.

**Ele serve a dois leitores.** Se você é uma **pessoa** adotando sozinha, pule para
*Qual é o seu caso* — daqui até o fim tem tudo de que você precisa, e nenhum passo
depende de agente. Se você é o **agente** e pediram para guiar, a próxima seção é sua e
vem antes de qualquer outra coisa.

---

## Se você é o agente e pediram para guiar

Estas regras valem mais que o resto do documento, e o resto é o conteúdo que você vai
usar para cumpri-las.

1. **Descubra em vez de perguntar.** Qual é o caso, se há produto na pasta, se o estado
   já foi preenchido — está tudo no disco. Rode e veja.
2. **Uma instrução por vez.** Diga o próximo passo, espere acontecer, confira, siga. Não
   despeje os seis passos de uma vez.
3. **Não explique o método.** Quem está adotando quer adotar. O porquê está no
   `metodo/METODO.md`, e só entra se for perguntado.
4. **Não declare protocolo aqui.** Durante a adoção o índice está vazio: consultá-lo é
   teatro, e anunciar que consultou é ruído.
5. **Não discuta a condução.** Se pediram para guiar, guie.
6. **Pergunte só o que não está no disco** — o nome do projeto, onde mora o material, o
   que um documento é. Nada além disso.

**Como saber onde você está, sem perguntar:**

| O que você observa | Onde está | O que fazer |
|---|---|---|
| `CLAUDE.md` com `{NOME DO PROJETO}` e `metodo/modelos/` presente | no template | primeiro passo é `python -m metodo novo` |
| `CLAUDE.md` já nomeado, `python -m metodo check` diz *adoção incompleta* | adoção em curso | siga do passo que falta |
| `python -m metodo check` sem *adoção incompleta* | adoção terminou | ofereça `rm COMO-ADOTAR.md` |

**A única pergunta que abre a condução**, quando você está no template:

> Qual o nome do projeto?

Com ela você roda o `python -m metodo novo` e o resto se descobre.

---

## Qual é o seu caso

### A — Projeto novo

Você parte do **clone do template**, e é de dentro dele que roda:

```bash
python -m metodo novo "Meu Projeto"                  # cria ../meu-projeto
python -m metodo novo --caminho "C:/projetos/meu-projeto"   # ou informe o caminho completo
```

O comando cria a pasta, copia o método, dá o nome ao `CLAUDE.md`, zera o `state/` e gera
o índice — o projeto nasce com `python -m metodo check` limpo. Depois, na pasta nova: `git init -b
main`, abra o agente e diga **"leia o `COMO-ADOTAR.md` e me guie na adoção"**.

Ponha em `refs/` só o que **outra pessoa mantém**. `docs/` nasce vazio e cresce sozinho.

### B — Projeto que já existe ← **a maioria das adoções**

**Antes, no projeto: `git status` limpo.** Se não estiver, commite o trabalho pendente à
parte. A adoção sai num commit próprio e reversível, sem misturar com o que é seu.

```bash
cd ai-project-framework
python -m metodo adotar ../meu-projeto "Meu Projeto"
```

**Nada é sobrescrito.** O comando confere o destino antes de escrever e, se algum arquivo
do método já existe lá com outro conteúdo, lista e para. O método mora inteiro na pasta
`metodo/` e roda por `python -m metodo`: **o seu `Makefile` não é tocado**, e `make
index`, `make check`, `make clean` continuam sendo só seus. Os três arquivos que todo
projeto já tem recebem tratamento próprio:

- **`CLAUDE.md`**: o seu vira `CLAUDE.anterior.md`, e a `AD-03` manda mesclá-lo no novo;
- **`.gitignore`**: recebe só as linhas do método que faltam;
- **`.gitattributes`**: copiado se você não tiver um.

Ele também avisa — sem recusar — sobre árvore suja e arquivo grande fora do git, que o
primeiro `git add -A` publicaria. Depois chama o `bootstrap`, que dá o nome ao
`CLAUDE.md`, cria o `state/` e gera o índice. **Ele não toca no seu `README.md`.**

**Seus documentos ficam onde estão** — não mova nada ainda. Só vai para `refs/` o que
vem de fora, e a distribuição é a `AD-02`.

Ninguém adota um método de continuidade num projeto que ainda não durou o suficiente
para doer. Se você está aqui, é quase certo que seja o caso B.

---

## Depois de criar a pasta: a ordem

Se você abriu o agente e pediu *"leia o `COMO-ADOTAR.md` e me guie na adoção"*, **é este
o roteiro**. As seções seguintes são o detalhe de cada passo, não leitura obrigatória em
ordem.

**A adoção são três passos.** Eles já estão escritos como pendências em
`state/aberto.md`, com o prefixo `AD-` — risque conforme fizer.

1. **`AD-01` — Traga o produto para a pasta.** O `.pbip`, o código, os notebooks: o que
   o projeto entrega. A pasta nasce só com o método, e nada mais faz sentido sem ele.
2. **`AD-02` — Aponte onde está o material que você já tem**, sem mover nada. O agente lê
   de onde estiver, propõe destino item a item, e roda `python -m metodo index`. Ver *Onde vai cada
   coisa*.
3. **`AD-03` — Preencha "O que é este projeto"** no `CLAUDE.md`: duas ou três frases.

**Acabou.** Rode `python -m metodo check` e vá trabalhar.

As pendências `AD-04` a `AD-06` **não são adoção** — são a ponte para o projeto, e cada
uma acontece no seu momento: o primeiro handoff real ao fechar a primeira sessão que
produziu fato novo (commit, medição, decisão, suspeita) — que pode ser a própria
adoção —, a tabela de roteamento quando você já souber quais tipos de mudança este
projeto tem, e a limpeza dos vestígios quando as outras caírem.

**Por que o estado não entra na adoção:** quem adota pela primeira vez ainda não conhece
os papéis dos documentos — vai aprender trabalhando. Pedir o estado agora é pedir uma
síntese antes de existir vocabulário para fazê-la. E adoção que vira burocracia não
sobrevive à primeira semana.

**No caso B**, a pasta já existe e já tem o produto: risque a `AD-01` e comece na
`AD-02`.

---

## Onde vai cada coisa

A dúvida que trava toda adoção: você chega com ata em Word, um `NOTAS.md` com tudo
misturado, planilha de pendências, decisão enterrada em comentário de código. Esse
material é **seu** — logo não é `refs/` — mas não está em forma de registro — logo
ainda não é `docs/`.

**Antes do critério, uma separação que ele não cobre: o produto não é documento.** O
`.pbip`, o código, os notebooks — o que o projeto entrega — ficam na raiz do projeto,
versionados como qualquer fonte. `docs/`, `refs/` e o arquivo morto são para o que **fala
sobre** o produto.

**O critério de destino, em uma linha:**

> **Quem mantém o documento?** Eu → `docs/`. Alguém de fora → `refs/`. Ninguém, mas
> não se joga fora → arquivo morto, fora do índice.

**E o que fazer com a bagunça:** não mova nada primeiro. Aponte o agente para onde o
material está — onde quer que esteja — e peça a distribuição:

> "Leia o que está em `<caminho>` e proponha o destino de cada item: o que vira ADR,
> o que vira dívida técnica, o que é ata e não vira nada, o que é de fora e vai para
> `refs/`. Vou aprovar item a item."

Ele lê e propõe; você aprova. O passo **destila**, não move. O original fica onde
estava, ou é descartado, porque o valor migrou.

### E o que não é nenhum dos três

Documento superado que ainda assim não se joga fora — a definição íntegra de um objeto
removido, a especificação de uma funcionalidade desativada, um registro avulso já
transcrito para o consolidado. Não é `docs/`, porque ninguém consulta na operação
normal e não tem status vivo. Não é `refs/`, porque é seu.

A convenção é uma pasta `arquivo-morto/` na raiz, com um contrato de três linhas:
**não entra no índice, não é consultada na operação normal, e não é apagada.** A
pergunta que decide a entrada: *se alguém pedir isto de volta daqui a um ano, eu
consigo reconstruir sem?* Se não, arquiva.

**O template não traz essa pasta, e é deliberado.** Três razões, para você não a
procurar achando que faltou:

- Git não versiona pasta vazia, então shipá-la obrigaria a shipar um README dentro —
  mais um documento em **todo** projeto adotado, para uma pasta que a maioria nunca vai
  usar. O `refs/` paga esse custo porque é necessário no dia 1 por todo mundo; esta só
  passa a existir depois que algo é superado.
- **O git já preserva.** Toda versão apagada está no histórico. O que a pasta acrescenta
  não é preservação, é navegabilidade — poder olhar sem saber o que procurar nem quando
  sumiu. É valioso, mas é menos do que parece.
- Prever um lugar de descarte é prever descarte. O template não deve se ocupar disso.

Crie quando precisar, com esse nome e esse contrato. Como o índice só varre `docs/` e a
lista `EXTRA_SOURCES`, ela já nasce fora dele — nenhuma configuração é necessária.

---

## Escrever o `state/` — primeira sessão de trabalho, não adoção

**Isto não é passo de adoção.** É o que acontece ao fechar a primeira sessão que
produziu fato novo sobre o projeto, e é a `AD-04`. O critério é o fato, não o
calendário: se a sessão da adoção teve commit, medição ou decisão, o handoff de
transição já ficou falso, e o real se escreve nela.

O `python -m metodo init` copia os **modelos vazios**. Preencher é o que separa *"instalei o
template"* de *"adotei o método"* — e é o passo mais demorado e de maior valor da
adoção inteira.

- **`handoff.md`** — escreva a partir de **onde o projeto está hoje**, não a partir do
  modelo. É o teste de aceitação: se alguém consegue retomar o projeto lendo só ele,
  a adoção terminou.
- **`aberto.md`** — as pendências que já existem, mesmo as que só estão na sua cabeça.
- **`changelog.md`** — se o projeto tem histórico, pode ser reconstruído do que
  existir: relatórios, commits, atas. Não precisa ser completo, precisa ser verdadeiro.

É a única parte que não dá para automatizar, e é a que paga a adoção inteira. O
`python -m metodo check` avisa enquanto o handoff ainda for o modelo.

---

## O primeiro `python -m metodo index` é diagnóstico, não configuração

Também para o caso B. No projeto novo ele gera um índice vazio e pronto; num projeto
que já existe, **o número que ele imprime é uma medição do seu passivo**.

Compare com quantos registros você acha que tem. A diferença é o que ninguém estava
conseguindo consultar.

> Numa adoção real, a primeira geração encontrou **55 registros**. Depois de ajustar o
> formato dos cabeçalhos, encontrou **130**. Três quintos da documentação estavam
> inalcançáveis pelo passo 1 do protocolo, havia semanas, e ninguém sabia.

O `python -m metodo check` ajuda aqui: ele aponta cabeçalho que **quase** casa com o padrão
`## ID — Título` e por isso ficou de fora. Um separador errado — ponto médio no lugar
do travessão — é a diferença entre documentado e invisível.

---

## Trazer as especificações

```bash
cp ~/onde/estiver/* refs/
python -m metodo intake
```

A pasta `refs/` já vem no template, vazia. É onde moram as especificações do projeto —
o que define o que precisa ser entregue, e que o agente lê mas nunca edita. A definição
completa e o fluxo de derivação estão em [`refs/README.md`](refs/README.md).

Faça isto **antes** da primeira sessão: com a especificação em mãos, o agente preenche
o `CLAUDE.md` com o vocabulário do seu domínio em vez de inventar um.

---

## A primeira sessão

Abra o agente na pasta do projeto e cole isto:

> Este projeto acabou de adotar o template. Leia o `CLAUDE.md` e me ajude a completar as
> três partes que faltam.
>
> 1. **O que é este projeto** — marcada com `{...}`. Vou te contar; escreva em duas ou
>    três frases, mais ambiente e IDs se houver. Credencial nunca.
> 2. **Regra de roteamento** — a tabela veio genérica. Me pergunte quais tipos de mudança
>    este projeto realmente tem e ajuste a coluna da esquerda. Se algum tipo não tiver
>    destino claro, é sinal de que falta um documento canônico — me diga qual.
> 3. **Convenções do projeto** — marcada com `{...}`. Deixe vazia por enquanto e me
>    explique quando uma linha deve ser acrescentada aí.

**Duas das três estão marcadas com `{...}`** no arquivo; a do meio é uma tabela a
ajustar, e não tem marcador nenhum.

Sobre *Convenções do projeto*: comece vazio. Essa seção **cresce sozinha** — toda vez
que uma armadilha custar tempo, ela vira uma linha ali. É o que impede o mesmo erro na
terceira vez.

---

## Autorizar as tarefas automáticas do VS Code

O template traz `.vscode/tasks.json`, que roda `claude -c` ao abrir a pasta e retoma a
conversa anterior. **Mas o VS Code bloqueia tarefas automáticas até você autorizar** —
e sem esse passo o arquivo não faz nada. O sintoma é "sempre abre uma sessão nova":

1. Abra a pasta no VS Code
2. Command Palette → **Tasks: Allow Automatic Tasks**
3. Feche e reabra a pasta

A alternativa ampla, `"task.allowAutomaticTasks": "on"` no settings do usuário, tem uma
ressalva: passa a executar tarefas de **qualquer** pasta que você abrir, incluindo
repositório de terceiro recém-clonado. Autorizar por pasta é mais seguro.

Sem VS Code, o equivalente é `python -m metodo session`.

---

## Todo dia: o ritual de fechamento

Não é opcional — é o que faz o método funcionar na próxima sessão.

```
1.  registrar a mudança em state/changelog.md      (append, no momento em que acontece)
2.  atualizar state/aberto.md                      (pendência nasce e é riscada)
3.  regenerar state/handoff.md do zero             (teto ~80 linhas)
4.  python -m metodo index                                     (se algum canônico mudou)
5.  python -m metodo check                                     (confirmar que está tudo de pé)
6.  commit
```

A ordem importa, e não é estilo — é dependência. Duas delas, em particular:

**O handoff é derivado do changelog.** Feche o changelog primeiro: o handoff copia o que
encontrar, inclusive o que faltar.

**A pendência é riscada antes do commit, não depois.** O commit é o passo 6 porque ele
**publica um estado consistente**, e não porque marca a conclusão do trabalho. Riscar
depois produziria um commit em que o `changelog.md` diz "resolvida" e o `aberto.md` ainda
a mostra aberta — o repositório contradizendo a si mesmo no meio do histórico.

**Commit ao fim de cada sessão.** Commits diários ficam atômicos e o `git log` vira
relatório; acumular dias produz commits com tipos misturados.

Se alguma mudança ficou **sem documentar**, registre isso em destaque no handoff — a
próxima sessão começa por aí.

---

## Opcional: conectar MCP

```bash
cp .mcp.json.example .mcp.json                 # escopo do projeto, versionável
claude mcp add <nome> -- <comando>             # escopo local
claude mcp add -s user <nome> -- <comando>     # escopo usuário: todos os projetos
python -m metodo mcp-list
```

Integração que serve a **todos** os seus projetos — gestão de tickets, API interna —
vale em escopo de usuário: existe uma instância, e melhorar uma vez chega em todos.
Regras e critério em [`mcp/README.md`](mcp/README.md).

---

## Terminar a adoção

A adoção termina quando **`AD-01`, `AD-02` e `AD-03` estão riscadas** em
`state/aberto.md`: produto na pasta, documentação distribuída e indexada, projeto
descrito em duas ou três frases.

O `python -m metodo check` vai continuar avisando que o estado do projeto não foi escrito. **Isso é
correto e não é pendência de adoção** — é a `AD-04`, e ela se resolve no fim da primeira
sessão de trabalho.

Quando as três caírem, este arquivo cumpriu o papel dele:

```bash
rm COMO-ADOTAR.md
```

Ele viajou junto **para ser consumido**. Depois de adotado, o procedimento de adoção só
ocuparia espaço no projeto — e a próxima pessoa que precisar dele pega no template, que é
onde ele é mantido.

---

## O que esperar

O ganho não aparece no primeiro dia — aparece quando a sessão é retomada. Ler 100
linhas de `handoff` + `aberto` reconstrói semanas de contexto por uma fração do custo
de reler conversa. E a documentação para de apodrecer porque a regra de roteamento
obriga a atualizar **na mesma sessão da mudança**, não depois.

## O que não esperar

Isto não substitui revisão humana. O agente vai errar; o método faz o erro aparecer
mais cedo — nas validações, no índice defasado, na pendência que não foi riscada.

E **o template não se propaga sozinho**: um projeto que adota fica com cópias de
`CLAUDE.md` e `metodo/`, e melhoria feita no template depois não chega por conta própria.
Para levá-la, a partir do clone novo do template:

```bash
python -m metodo atualizar ../meu-projeto --simular   # mostra o plano, não grava
python -m metodo atualizar ../meu-projeto             # aplica; exige git status limpo
```

Ele troca o que é do método (`metodo/`, e os restos das versões antigas: `tools/`,
`.template/`, `metodo.mk`, os alvos do método no `Makefile`), reescreve no `CLAUDE.md` as
citações aos comandos antigos e deixa como pendência `AT-`, no `state/aberto.md`, o que
pede julgamento: texto novo do método a mesclar (o modelo vem em
`metodo/CLAUDE.modelo.md`) e citações em documentos do projeto. Não toca em `state/` nem
em `docs/`, e reconhece alvo do método **pelo que ele executa**: o `make index` que
constrói o seu índice vetorial continua sendo seu. O `metodo/VERSAO` diz de qual versão
cada projeto veio.

E **o modo de trabalho não viaja junto com o repositório.** O que o agente aprendeu
sobre você fica no perfil do usuário, indexado pelo caminho do projeto na sua máquina —
um colega que clonar recebe um agente sem nada disso. O repositório estaria certinho; o
modo de trabalho, não. Por isso toda preferência durável que o time precisa herdar tem
de ser espelhada em *Modo de trabalho*, no `CLAUDE.md`. O custo de não fazer é
assimétrico: quem escreveu não sente falta, e só quem herda descobre.
