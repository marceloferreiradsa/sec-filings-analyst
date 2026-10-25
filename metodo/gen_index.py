#!/usr/bin/env python3
"""Regenera docs/_index.md varrendo os documentos canonicos.

O indice existe para permitir LEITURA DIRIGIDA: em vez de carregar um documento
inteiro para achar um registro, o agente consulta o indice e le so o trecho.
Isso e o que mantem o consumo de contexto baixo.

O que o indice carrega, e por que:

    ID       para citar o registro sem ambiguidade — e para acha-lo
    Titulo   para busca por palavra-chave, que e o passo 1 do protocolo
    Status   porque o protocolo decide com ele: status resolvido -> PARAR.
             Sem status aqui, o agente teria de abrir o documento so para
             saber se deve parar, e o indice perderia a razao de existir

O que ele NAO carrega, e por que:

    Numero de linha. Era a unica parte do indice capaz de ficar falsa em
    silencio: qualquer edicao acima de um registro desloca todos os seguintes,
    e nada avisa. Titulo errado alguem percebe lendo; linha errada manda para o
    lugar errado sem aviso. O endereco passa a ser o proprio ID, que ja e unico
    e ja esta no cabecalho do registro:

        grep -n "^## ADR-07" docs/decisoes_arquiteturais.md

    Custa uma chamada barata e nao pode estar desatualizado, porque nao e
    armazenado em lugar nenhum.

    Contagens e qualquer copia de conteudo — "um fato, um lugar" aplicado ao
    proprio indice.

Consequencia pratica: o indice so fica defasado quando um registro nasce, morre,
muda de titulo ou muda de status — exatamente os momentos em que a regra de
roteamento ja obriga a toca-lo. Reescrever um paragrafo no meio de um canonico
deixou de defasar o indice.

Padrao reconhecido: cabecalhos de nivel 2 ou 3 que comecam com um identificador
seguido de travessao. Exemplos:
    ## ADR-07 — Titulo da decisao
    ### DT-03 — Titulo da divida
    ### I.11 — Titulo do gap
Configuravel em PATTERN, abaixo.

O indice cobre TAMBEM a especificacao, nao so a documentacao propria. Todo
projeto tem um documento que ele nao mantem — manual do cliente, contrato, RFC —
e que e a fonte da verdade sobre o que precisa ser entregue. Se voce consulta,
indexa: caso contrario ele fica invisivel ao protocolo, e voce reconstroi por
investigacao respostas que ja estavam escritas ali. Configuravel em
EXTRA_SOURCES. Esses documentos raramente seguem a convencao "ID — Titulo",
entao sao varridos com LOOSE_PATTERN, que indexa qualquer cabecalho.
"""
import re
import sys
from pathlib import Path

# Windows: sem isto, o stdout sai em cp1252 e corrompe os acentos das mensagens.
sys.stdout.reconfigure(encoding="utf-8")

DOCS = Path("docs")
INDEX = DOCS / "_index.md"

# ID = letras/numeros/pontos/hifens, seguido de travessao ou hifen
PATTERN = re.compile(r"^(#{2,3})\s+([A-Za-z0-9][A-Za-z0-9._-]*)\s+[—–-]\s+(.+?)\s*$")

# Status declarado no corpo do registro, na convencao dos modelos deste template
STATUS = re.compile(r"^\*\*Status:\*\*\s*(.+?)\s*$")

# Prioridade sobe junto: e por ela que se decide o que endereçar antes. Assim o
# documento nao precisa manter um indice por prioridade a mao — que apodrece.
PRIORIDADE = re.compile(r"^\*\*Prioridade:\*\*\s*(.+?)\s*$")

# Qualquer cabecalho: marca onde termina o corpo de um registro
ANY_HEADING = re.compile(r"^#{1,6}\s")

# Documentos ignorados na varredura (o proprio indice e leituras auxiliares)
SKIP = {"_index.md", "README.md"}

# Diretorios fora de docs/ que tambem entram no indice: a especificacao, o
# contrato, o manual do cliente. Varridos com LOOSE_PATTERN porque nao seguem a
# convencao de ID do projeto. Deixe a lista vazia se nao houver.
EXTRA_SOURCES = ["refs"]

# Qualquer cabecalho de nivel 2 ou 3, sem exigir identificador. Desce ao nivel 3
# de proposito: em especificacao, o requisito costuma morar na subsecao.
LOOSE_PATTERN = re.compile(r"^#{2,3}\s+(?![`#])(.+?)\s*$")

BARRA = chr(124)
ESCAPE = chr(92) + chr(124)


def campo_de(lines, i, padrao):
    """Campo rotulado no corpo do registro cujo cabecalho esta em lines[i].

    Rotulo curto: o que vem depois do primeiro ponto e comentario, pertence ao
    documento e nao ao indice.
    """
    for line in lines[i + 1:]:
        if ANY_HEADING.match(line):
            break
        m = padrao.match(line)
        if m:
            return m.group(1).split(".")[0].strip()[:48]
    return ""


def escapar(texto):
    return texto.replace(BARRA, ESCAPE)


def scan():
    found = {}
    for doc in sorted(DOCS.glob("*.md")):
        if doc.name in SKIP:
            continue
        lines = doc.read_text(encoding="utf-8").splitlines()
        entries = []
        for i, line in enumerate(lines):
            m = PATTERN.match(line)
            if m:
                entries.append({"id": m.group(2), "title": m.group(3),
                                "status": campo_de(lines, i, STATUS),
                                "prioridade": campo_de(lines, i, PRIORIDADE)})
        if entries:
            found[doc.as_posix()] = entries

    for base in EXTRA_SOURCES:
        root = Path(base)
        if not root.is_dir():
            continue
        for doc in sorted(root.glob("*.md")):
            if doc.name in SKIP:
                continue
            entries = []
            for line in doc.read_text(encoding="utf-8").splitlines():
                m = LOOSE_PATTERN.match(line)
                if m:
                    entries.append({"id": m.group(1), "title": "",
                                    "status": "", "prioridade": ""})
            if entries:
                found[doc.as_posix()] = entries
    return found


H1 = re.compile(r"^#\s+(.+?)\s*$")
SECAO = re.compile(r"^##\s")


def sem_registros():
    """[(caminho, h1, n_secoes)] dos documentos de docs/ sem nenhum registro.

    Documento de procedimento (pipeline, deploy, guia) e vivo e consultado, mas
    nao tem registro, e por isso nao aparecia no indice — que e onde o agente
    procura antes de tudo. E o mesmo sinal pega formato de registro que o
    PATTERN nao reconhece: 15 secoes e zero registros nao e procedimento, e
    cabecalho fora do formato. Quem diz qual dos dois e o `python -m metodo check`."""
    achados = []
    if not DOCS.is_dir():
        return achados
    for doc in sorted(DOCS.glob("*.md")):
        if doc.name in SKIP:
            continue
        lines = doc.read_text(encoding="utf-8").splitlines()
        if any(PATTERN.match(line) for line in lines):
            continue
        h1 = next((m.group(1) for m in map(H1.match, lines) if m), "")
        achados.append((doc.as_posix(), h1, sum(1 for l in lines if SECAO.match(l))))
    return achados


def render(found):
    out = [
        "# Índice dos documentos canônicos",
        "",
        "> **Arquivo derivado — nunca editar a mão.** Gerado por `python -m metodo index`",
        "> (`metodo/gen_index.py`), varrendo os cabeçalhos de `docs/`.",
        ">",
        "> **Para que serve:** permitir leitura dirigida. Ache o registro aqui pelo",
        "> título ou pelo status, e leia só o trecho — em vez de carregar o documento",
        "> inteiro. Para chegar ao registro, procure o ID no arquivo indicado, com",
        "> `grep -n` pelo cabeçalho.",
        ">",
        "> **Não há número de linha aqui, de propósito.** Era a única informação capaz",
        "> de ficar falsa em silêncio, porque qualquer edição acima de um registro",
        "> desloca todos os seguintes. O ID é o endereço, e ele não se desloca.",
        ">",
        "> **Cobre a especificação, não só a documentação própria.** Manual do cliente,",
        "> contrato ou RFC entram aqui pela lista EXTRA_SOURCES do gerador. Documento de",
        "> fora do índice é documento que ninguém lê no momento certo.",
        "",
        "---",
        "",
    ]
    for path, entries in found.items():
        out += ["## `" + path + "`", ""]
        if entries and entries[0]["title"] == "":
            out += ["| Entrada |", "|---|"]
            for e in entries:
                out.append("| " + escapar(e["id"]) + " |")
        else:
            # Coluna opcional so aparece se algum registro do arquivo a preencher:
            # coluna vazia para todo mundo e ruido no lugar mais lido do metodo.
            opcionais = [(rotulo, chave) for rotulo, chave
                         in (("Status", "status"), ("Prioridade", "prioridade"))
                         if any(e[chave] for e in entries)]
            out += ["| ID | Título |" + "".join(" " + r + " |" for r, _ in opcionais),
                    "|---|---|" + "---|" * len(opcionais)]
            for e in entries:
                linha = "| " + e["id"] + " | " + escapar(e["title"]) + " |"
                for _, chave in opcionais:
                    linha += " " + escapar(e[chave]) + " |"
                out.append(linha)
        out += ["", ""]
    # Sem contagem de secoes aqui: o indice guarda o minimo para achar e decidir,
    # nunca numero que muda a cada edicao. A contagem vive na saida do check.
    sem = sem_registros()
    if sem:
        out += ["## Documentos sem registros", "",
                "> Vivem em `docs/` sem nenhum cabeçalho `ID — Título`: procedimento,",
                "> guia, narrativa. Estão aqui para que se saiba que existem.", "",
                "| Documento | Título |", "|---|---|"]
        for caminho, h1, _ in sem:
            out.append("| `" + caminho + "` | " + escapar(h1) + " |")
        out += ["", ""]
    total = sum(len(v) for v in found.values())
    out += ["---", "", "*" + str(total) + " registros em "
            + str(len(found)) + " documentos.*", ""]
    return "\n".join(out)


def check_index():
    """Compara o indice gravado com o que seria gerado agora. 0 = em dia."""
    if not INDEX.exists():
        print("  DEFASADO: docs/_index.md não existe. Rode 'python -m metodo index'.")
        return 1
    if INDEX.read_text(encoding="utf-8").strip() != render(scan()).strip():
        print("  DEFASADO: o índice não reflete os documentos. Rode 'python -m metodo index'.")
        return 1
    print("  ok     índice em dia")
    return 0


def main():
    if not DOCS.is_dir():
        print("  docs/ não existe — rode 'python -m metodo init' primeiro")
        return 1
    found = scan()
    new_text = render(found)

    if "--check" in sys.argv:
        return check_index()

    if "--write" in sys.argv:
        # O argumento newline abaixo e obrigatorio: sem ele o Python traduz o fim
        # de linha para CRLF no Windows, o .gitattributes pede LF, e o git avisa
        # a cada `python -m metodo index`.
        INDEX.write_text(new_text, encoding="utf-8", newline="\n")
        return 0

    print(new_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
