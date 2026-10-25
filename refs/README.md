# `refs/` — as especificações do projeto

Esta pasta guarda as **especificações feitas pelo cliente, usuário final do
produto/serviço gerado pelo projeto e/ou decididas em conjunto com a área de
desenvolvimento**. Também entram contrato, RFC, manual, dicionário de dados e export
de planilha — tudo que define o que precisa ser entregue.

O que separa esta pasta de `docs/` não é quem trouxe o arquivo: é **quem tem
autoridade para alterá-lo**. Aqui, não é o agente.

> **Regra única desta pasta: o agente lê, nunca edita.**
> Se algo está errado no original, a correção vira nota em documento canônico
> (`docs/`), não edição aqui. O original tem que continuar comparável com a
> cópia que o cliente tem na mão.

A pasta já vem no template, vazia de propósito. Ela existir é o lembrete de que
a especificação precisa entrar — pasta que não existe não lembra ninguém de nada.

## Por que isto importa mais do que parece

O índice (`docs/_index.md`) é o que o agente consulta no passo 1 do protocolo,
antes de qualquer ação. **O que não está no índice é invisível para esse passo.**
E PDF e planilha não entram no índice: são caros de ler e não têm cabeçalho que
o gerador reconheça.

Consequência prática: enquanto a especificação não tiver uma versão em markdown
indexada, ela não existe para o agente. Ele vai reconstruir por investigação —
por dias — respostas que já estavam escritas ali. Essa falha é a origem
documentada da regra; está contada em `metodo/METODO.md`, na seção do índice derivado.

## Como usar

**1. Copie os arquivos para cá.**

```bash
cp ~/onde/estiver/* refs/
```

**2. Rode o conferidor.**

```bash
python -m metodo intake
```

Na primeira vez ele cria `refs/_fontes.md`, o manifesto. Depois, a cada rodada,
ele confere arquivo por arquivo e aponta três coisas: arquivo que não está
declarado, declaração que não tem arquivo, e original pesado que ainda não tem
versão derivada.

**3. Preencha o manifesto à mão.**

`refs/_fontes.md` é o único arquivo desta pasta que você escreve. Uma linha por
arquivo: o que é, e onde está a versão derivada.

Ele é escrito à mão, e não gerado, por um motivo específico: **parentesco entre
um PDF e o markdown que saiu dele não é adivinhável por nome de arquivo.** O
script confere o que você declarou; ele não tenta descobrir sozinho.

**4. Derive o que o `python -m metodo intake` marcar como `DERIVAR`.**

Peça ao agente:

> "converta este arquivo de `refs/` em markdown indexado, preservando a
> numeração de seção e a paginação do original, e registre o derivado em
> `refs/_fontes.md`"

Preservar a paginação importa: a mesma citação passa a servir nos dois lados —
você cita a página do PDF numa reunião enquanto o agente lê o markdown.

**Derivado não precisa ser conversão literal.** Uma planilha de verificações
rende mais como registro com status por item do que como transcrição, porque
planilha é binária e não é alcançável por busca de texto.

**5. Indexe.**

```bash
python -m metodo index
```

Os markdown de `refs/` entram no índice pela lista `EXTRA_SOURCES` do
`metodo/gen_index.py`. Eles são varridos com um padrão mais frouxo que o dos
canônicos, porque especificação de terceiro raramente segue a convenção
`## ID — Título` do projeto.

## O que não colocar aqui

- **Documento que é seu.** Se você escreve e mantém, o lugar é `docs/`.
- **Credencial, chave, token.** Nunca, em nenhuma pasta.
- **Insumo do produto** — corpus, dataset, dump —, mesmo que mantido por terceiros.
  `refs/` é o que define o que entregar, não o que o produto processa. O critério de
  autoridade não separa os dois: o PDF de onde o RAG extrai é de outra pessoa, e ainda
  assim é matéria-prima, não requisito.
- **Arquivo que ninguém vai consultar.** Se não vale indexar, não vale guardar
  aqui: vira ruído no `python -m metodo intake` para sempre.

## Este README

É documentação do método, não fonte externa. O `python -m metodo intake` e o `python -m metodo index`
ignoram este arquivo de propósito — ele não aparece no manifesto nem no índice.
