# O método — por que cada peça existe

> Este documento guarda o **raciocínio**. O `README.md` diz o que é; o
> `COMO-ADOTAR.md` diz como começar; aqui está por que funciona.
>
> Cada regra abaixo nasceu de uma falha concreta. As histórias de origem não são
> enfeite: são o que permite julgar se a regra se aplica ao seu caso, e o que
> permite reconstruir o método se este repositório se perder.

---

## O problema

Trabalhar com um agente em projeto que dura semanas esbarra em três limites que
se reforçam:

1. **A janela de contexto é finita.** Conversa longa acaba truncada ou resumida, e
   o que se perde nunca é o que você escolheria perder.
2. **Crédito é finito.** Reler histórico para lembrar onde parou é o gasto mais
   caro e menos útil possível.
3. **Documentação apodrece.** Se atualizar depende de disciplina, não acontece — e
   documentação errada é pior que ausente, porque induz decisão.

A resposta usual é manter a conversa aberta. Não funciona: o custo cresce sem
limite e o contexto morre junto com a sessão.

---

## A ideia central

**A continuidade não vem do histórico do chat. Vem de arquivos de estado com
contrato definido.**

Ao abrir uma sessão, o agente lê dois arquivos — cerca de 100 linhas — e
reconstrói semanas de trabalho. Não relê conversa nenhuma.

Isso inverte a economia: o custo de retomar deixa de crescer com o tempo do
projeto e passa a ser **constante**. E o método sobrevive a sessão encerrada,
troca de máquina, troca de pessoa.

---

## Os quatro elementos

### 1. Estado — `state/`

| Arquivo | Contrato | Falha que previne |
|---|---|---|
| `handoff.md` | Onde paramos. **Regenerado do zero** ao fim de cada sessão, teto ~80 linhas | Arquivo de estado que só cresce vira depósito e ninguém lê |
| `aberto.md` | Pendências vivas, escritas ao nascer e **riscadas ao morrer** | Lista que ninguém volta para riscar apodrece descrevendo como pendente algo já feito |
| `changelog.md` | **Append-only**, uma entrada por mudança, no momento em que acontece | Git mostra o que mudou; só o changelog guarda **por que** |

**A ordem é dependência, não estilo.** O handoff é gerado **a partir do** changelog.
Fechar o changelog primeiro não é capricho de ritual: o handoff **copia o que
encontrar**, e um changelog incompleto propaga em silêncio para o arquivo mais lido do
método. Lido como lista de tarefas, a ordem parece arbitrária — e listas de tarefas se
executam fora de ordem.

**Origem:** num fechamento de dia, o handoff quase foi regenerado de um changelog a que
faltavam duas entradas. Só não aconteceu porque o changelog foi aberto por acaso, para
outra coisa.

**O commit vem por último pelo mesmo motivo, e isso costuma ser lido ao contrário.** A
tentação é riscar a pendência depois de commitar, como se o commit fosse o que conclui o
trabalho. Não é: o trabalho termina quando a correção está escrita e verificada, e o
commit **embrulha changelog, risco e handoff num estado consistente**. Riscar depois
deixaria no histórico um commit em que o changelog declara resolvido o que o `aberto.md`
ainda mostra aberto.

Quem for melhorar o ritual vai encontrar essa ordem e achar que pode trocá-la. Ela tem
trade-off — a janela entre riscar e commitar existe, e nela o repositório está adiantado
em relação ao histórico. É o lado barato do custo: um estado transitório na sua máquina,
em vez de uma contradição permanente no `git log`.

**Por que regenerado do zero importa:** editar o handoff incrementalmente parece
mais barato e é o começo do apodrecimento. Reescrever obriga a decidir o que ainda
importa. O teto de linhas existe pelo mesmo motivo.

**Origem:** num projeto anterior o arquivo equivalente ao handoff virou depósito de
400 linhas que ninguém lia. E o mapa de decisões descrevia como pendente um lote de
documentação já executado dias antes — porque ninguém voltou para riscar.

---

### 2. Índice derivado — `docs/_index.md`

Índice gerado mecanicamente com **ID, título e status** de cada registro dos
documentos canônicos. Sem número de linha, de propósito — o endereço é o próprio ID.

**Para que serve:** leitura dirigida. O agente acha o registro no índice pelo título ou
pelo status, procura o ID no arquivo indicado, e lê **o trecho** — não o documento
inteiro. É o que mantém o consumo de contexto plano mesmo com documentação que cresce.

**Por que gerado e nunca escrito a mão:** todo campo copiado do canônico para o
índice apodrece em silêncio quando é mantido por disciplina. Gerar dispensa a
disciplina.

**Origem:** aconteceu **três vezes** no projeto onde o método nasceu. Duas só foram
descobertas quando o agente foi abrir um trecho e ele não estava lá. A terceira
apareceu ao comparar o índice mantido a mão com o gerado: dizia linha 60 onde a
real era 62.

**O desfecho, em 26/08/2026.** Gerar o número de linha resolvia a defasagem, mas não
o incômodo: reescrever um parágrafo qualquer defasava o índice, e a regra de
roteamento carregava uma linha só para lembrar disso. O número de linha foi
**removido**. O endereço passou a ser o próprio ID, procurado com `grep` no arquivo
indicado — não pode ficar desatualizado porque não é armazenado em lugar nenhum. O
índice agora só defasa quando um registro nasce, morre, muda de título ou muda de
status, que são os mesmos momentos em que a regra de roteamento já obriga a tocá-lo.
*Seria falso se* os canônicos crescessem a ponto de o `grep` deixar de ser barato.

**O índice cobre a especificação, não só a documentação própria.** Todo projeto tem
um documento que ele não mantém — manual do cliente, contrato, RFC — e que é a fonte da
verdade sobre o que precisa ser entregue. Se você o consulta, indexe: caso contrário
ele fica invisível ao protocolo.

**Origem:** num projeto o manual do cliente ficou fora do índice por semanas. Nesse
período foram registradas duas dívidas técnicas sobre exatamente o assunto de uma
seção dele, e duas perguntas entraram na fila para o cliente — perguntas que ele já
havia respondido no próprio manual. Nenhuma falha de atenção: a seção era
inalcançável pelo passo 1. Indexar custou minutos.

**O índice não carrega ressalva.** Ele guarda ID, título e status — e só.
Alerta de leitura pertence ao documento que ele comenta: se dois ADRs se
contradizem, quem anota isso é o documento de ADRs, no próprio registro. Se falta um
canônico cobrindo um assunto, quem registra é `state/aberto.md`.

**Origem:** houve uma versão deste método com um `docs/_index.notas.md` — ressalvas
escritas à mão, injetadas no índice pelo gerador. Foi descartado em 2026-08-26 sem
nunca ter sido implementado. O argumento que decidiu: nota escrita à mão sobre
registro gerado não tem ligação mecânica com ele, e sobrevive calada ao registro que
comentava. É o mesmo modo de falha que justifica o índice ser derivado, reintroduzido
por uma porta lateral, dentro do arquivo que existe para eliminá-lo. Nenhum tipo de
ressalva ficou sem casa.

**Frescor: no momento da leitura, não no da escrita.** Editar canônico acontece
dezenas de vezes por dia; consultar o índice, poucas. Por isso a verificação está no
**passo 1 do protocolo** — antes de consultar — e não presa a cada edição. Se num dia
houver 40 edições e 3 consultas, roda 3 vezes.

---

### 3. Regra de roteamento

Uma tabela estática: **mudei X, atualizo Y**. Consultada a cada alteração.

**A regra que sustenta tudo: a atualização acontece na mesma sessão da mudança.**
Não existe backlog de documentação — porque backlog de documentação nunca é feito.

**Por que uma tabela e não bom senso:** bom senso esquece. A tabela transforma
lembrar de documentar em consultar uma linha, que é barato e verificável.

---

### 4. Protocolo de consulta antes de agir

Antes de qualquer ação nova — investigação, decisão, código — o agente:

1. Verifica o frescor do índice e consulta o tema
2. Se achar registro **resolvido**, **para** e reporta, em vez de propor alternativa
3. **Declara explicitamente** o que consultou e o que encontrou

O passo 3 é o que torna o protocolo verificável: se a frase não aparece, você sabe
que ele foi pulado e pode interromper.

**Origem:** num único dia foram propostas três verificações empíricas **já feitas** e
criados registros redundantes com decisões existentes. Custou créditos e retrabalho.

---

## As regras de conduta

Não são sobre arquivos — são sobre como agente e pessoa trabalham juntos.

**Discutir antes de codar.** Rejeitar um desenho custa uma frase; rejeitar código
pronto custa a sessão inteira.

**Hipótese marcada como hipótese.** Quando supor for inevitável, registrar como
dívida com o impacto dimensionado. Uma chave estrangeira adotada por hipótese virou
decisão registrada com a dívida ao lado — e a dívida dizia exatamente o que não
podia ser entregue enquanto ela não fosse confirmada.

**Verificar antes de afirmar — e verificar os três estados.** Campo existir não
significa campo útil:

| Estado | O que testar |
|---|---|
| Ausente | `IS NULL` |
| Presente mas zerado | `> 0` — coluna pode estar 100% preenchida e inteiramente zerada |
| Presente mas órfão | a chave existe, mas aponta para uma linha que não existe |

**Origem:** os três erros aconteceram na mesma semana. Um campo reportado como 100%
preenchido estava 100% zerado. Uma chave preenchida não resolvia em 39% dos casos.
E um `NOT (col > 0)` em SQL descartou silenciosamente mais de um milhão de linhas
com valor nulo, porque `NULL > 0` é desconhecido, não falso.

**A conclusão carrega o que a falsearia.** Medição é fato; conclusão é
interpretação — e as duas tendem a ser escritas com o mesmo tom. Ao registrar uma
conclusão, acrescentar inline a condição que a tornaria falsa: *"seria falso se X"*.

**Origem:** um registro afirmou que certa informação não existia na origem. Duas
horas depois, a verificação seguinte mostrou que existia, um nível abaixo, num campo
que o código lia e descartava. A regra de roteamento obrigou a **escrever** o achado;
nada obrigou a marcar que era conclusão de uma medição só, com alternativa não
testada. **Escrever o falseador é desenhar o teste** — ali o falseador seria
exatamente o teste que veio depois. E não é só fricção: aplicado a um achado sólido,
a conclusão sai reforçada em vez de bloqueada.

**O que a pessoa vai executar, o agente valida antes.** Célula de notebook, query,
script: verificar a sintaxe antes de entregar. Se o agente produz algo para rodar num
ambiente que ele não alcança, a única barreira é ele próprio. Em um único dia três
entregas saíram quebradas e duas chegaram até o usuário — uma delas era um escape que
virou caractere de controle e teria falhado em silêncio, sem erro nenhum.

**Número plausível é mais perigoso que número em branco.** Branco você vê; número
errado com ordem de grandeza crível entra em apresentação. Uma medida chegou a
mostrar margem de 100% porque o custo era zero.

---

## O que custa

Não vale fingir que é de graça.

- **Documentar na mesma sessão** cobra tempo no momento em que você quer avançar.
- **Regenerar o handoff** cobra 10 minutos no fim do dia, quando você já quer parar.
- **O protocolo** parece burocracia nos primeiros dias, porque o índice ainda está
  vazio e não há o que consultar.
- **O reflexo de criar documento novo quando o problema é de indexação.** Descobrir
  que um conhecimento não está sendo encontrado sugere escrever um documento; muitas
  vezes o remédio é só indexar o que já existe. Antes de propor documento novo,
  perguntar se o problema é de conteúdo ausente ou de conteúdo invisível.

O retorno só aparece na retomada — e cresce com a duração do projeto.

---

## As três objeções, na ordem em que aparecem

O argumento que sai naturalmente ao apresentar o método é *"economiza tokens"*. É
verdade e é fraco: soa a otimização, e otimização se adia. O argumento forte é outro, e
só aparece quando as objeções vêm — sempre nesta ordem.

### *"Mas o Claude não lembra sozinho?"*

Lembra enquanto a sessão vive, e a sessão morre. O que ele lembra é **a conversa**; o
que o método guarda é **o projeto**.

Essa é a distinção que convence, e não a de custo: uma conversa é sua e morre com você.
Um handoff é da empresa, e a próxima pessoa lê sem você.

### *"Então por que não cortar a conversa periodicamente, em vez de limpar tudo?"*

A intuição por trás é boa, e revela o que a pessoa realmente quer: **ver o último dia**.
Vale responder nas duas camadas.

**Por que o corte não é o caminho.** Os cortes disponíveis são `/compact` e `/clear`;
existe controle de *quando* a compactação dispara (`claude --autocompact`, de 100k a 1M),
mas isso não é janela deslizante. E um corte cego seria pior do que parece, por três
motivos que não são óbvios:

1. **Chamada de ferramenta vem em par.** Cada chamada exige o resultado correspondente.
   Cortar no meio desemparelha os dois e invalida a conversa.
2. **O cache trabalha pelo começo.** O prefixo cacheado é o *início* da conversa.
   Descartar as mensagens mais antigas invalida exatamente esse prefixo, e o pedido
   seguinte reprocessa tudo. Um corte periódico pagaria *cache miss* toda vez:
   **custaria mais**.
3. **Corte cego joga fora a parte errada.** Uma janela do "último dia" descarta o mais
   antigo primeiro — e o começo costuma ser onde está o enquadramento da tarefa.
   Guarda-se a discussão de detalhe e perde-se a decisão que a originou.

**E por que ele já não é necessário.** O `handoff.md` **é** o último dia, e é melhor que
o transcript cru dele. O transcript traz os becos sem saída, as afirmações que
precisaram ser corrigidas, as versões de código que não sobreviveram. O handoff traz as
conclusões, em ~80 linhas escritas de propósito. Não é um substituto pior do último dia:
é o último dia **editado por quem sabia o que importava**.

A compactação, por sua vez, **paga tokens para resumir** — lê todo o contexto para
produzir o resumo — e o resumo ainda perde detalhe. O handoff já está escrito e custou
zero token extra, por ser subproduto do trabalho.

### *"Vou perder semanas de conversa"*

Esse medo é real e não deve ser tratado como resistência a vencer. Ele tem uma resposta
melhor do que "confie no handoff":

> **O `/clear` não apaga. Ele deixa de carregar.**

Os transcripts continuam no disco, um arquivo por sessão em
`~/.claude/projects/<projeto>/`, e `claude --resume` lista as sessões anteriores. É
afirmação verificável, não promessa: abra e confira.

Isso muda a natureza do pedido. Não se está pedindo à pessoa que **abra mão** do
histórico — está-se pedindo que **pare de pagar para carregá-lo em toda mensagem**. O
arquivo continua existindo para o dia em que ela quiser voltar; ela é que não o arrasta
a cada turno.

**A frase que resume o método inteiro:** a memória é o método em si. Se a janela ficar
grande, roda-se `/clear` e o contexto se reconstrói pelo protocolo — não porque se
confia na sorte, mas porque foi escrito.

---

## A rampa de adoção

Mandar alguém direto para o `/clear` é pedir um ato de fé antes de a pessoa ter
evidência. A rampa tem três degraus, e cada um produz a evidência do seguinte.

**1. `/compact` com instrução, no fim do dia.** Guarda um resumo e continua. Custa
tokens para resumir, mas é o degrau em que a pessoa **experimenta perder a conversa sem
perder de fato**.

**2. `/clear` com o handoff aberto ao lado.** A pessoa reabre, faz a pergunta que
importa, e confere se a resposta bate. É o degrau que converte — e vale escrever o
**gabarito antes** de rodar, com **duas listas separadas**:

- *o que o método tem de acertar* — o estado do projeto, as pendências, a última
  decisão e por quê;
- *o que ele não tem como saber* — o que só foi dito na conversa e nunca virou registro.

Sem a segunda lista o teste fica ambíguo, e a pessoa lê **perda de contexto esperada**
como falha do método. Com ela, o que falha aponta para uma lacuna real no `state/` — que
é justamente o que se quer descobrir.

**3. `/clear` por hábito**, quando a confiança já existe.

O degrau 1 custa tokens e é o único que o método, tecnicamente, dispensaria. Vale o
custo: adoção que pula a evidência não sobrevive à primeira semana ruim.

---

## Quando não usar

- **Tarefa de um dia.** O custo não se paga.
- **Projeto sem decisões** — script que só executa, sem escolhas com alternativa
  rejeitada. Sem decisão, não há o que registrar.
- **Exploração pura**, onde o objetivo é descobrir e não entregar.

O método pressupõe projeto que dura, tem decisões e tem consumidor.

---

## Como reconstruir do zero

Se este repositório se perder, o essencial em ordem de importância:

1. **Três arquivos em `state/`** com os contratos da tabela acima. Só isso já
   entrega a maior parte do valor.
2. **`CLAUDE.md`** com protocolo, regra de roteamento e economia de contexto.
3. **Gerador de índice** — script que varre os cabeçalhos dos documentos canônicos
   e emite ID, título e status. Cem linhas de Python.
4. **Makefile** amarrando `index` e `check`, com o `check` acusando índice defasado.

Os itens 1 e 2 são o método. Os itens 3 e 4 são o que impede o método de apodrecer.

---

## Por que funciona — em uma frase

Porque troca **memória** por **estado**: em vez de tentar lembrar, o projeto escreve
onde parou, e a escrita é obrigatória no momento em que a mudança acontece, não
depois.
