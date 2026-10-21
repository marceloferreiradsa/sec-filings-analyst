#!/usr/bin/env python3
"""Verifica o que falta, se o indice esta defasado e se a adocao terminou.

Roda a cada passo 1 do protocolo, entao e uma das saidas mais vistas do metodo —
motivo de estar aqui e nao como `@echo` no Makefile, que sai pela codepage do
terminal e corrompe acento no Windows.

Codigo de saida: falha quando o indice esta defasado ou quando o estado nao
acompanha o git. NAO falha por arquivo de metodo ausente, por cabecalho que
quase casa, nem por adocao incompleta — os tres sao normais durante a adocao, e
um check vermelho no primeiro dia ensina a ignorar o check.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import gen_index      # noqa: E402  (o diretorio do script entra no sys.path)
import intake         # noqa: E402
import check_state    # noqa: E402

ARQUIVOS = [
    "CLAUDE.md",
    "docs/_index.md",
    "state/handoff.md",
    "state/changelog.md",
    "state/aberto.md",
]

HANDOFF = Path("state/handoff.md")
MODELO_HANDOFF = Path(".template/handoff.md")

# Procura o marcador NO CAMPO, nao no texto: o handoff legitimamente cita
# "AAAA-MM-DD" em prosa ao descrever o formato do changelog, e buscar a
# string solta acusa quem esta certo. Simbolo nao e conceito.
GERADO_EM = re.compile(r"^\*\*Gerado em:\*\*\s*AAAA-MM-DD", re.M)

# Cabecalho que QUASE casa com o padrao de registro: comeca com um token que
# parece ID — tem digito — seguido de um separador que nao e travessao, meia
# risca nem hifen. O gerador ignora em silencio e o registro fica invisivel ao
# passo 1. Num projeto real isso deixou 37 achados fora do indice, por usarem
# ponto medio; um caractere separava "documentado" de "inalcancavel".
QUASE = re.compile(r"^#{2,3}\s+([A-Za-z0-9][A-Za-z0-9._-]*)\s*([^\w\s])")
SEPARADORES = "—–-"


def quase_casando():
    """{arquivo: [(linha, separador)]} dos cabecalhos que passaram perto."""
    achados = {}
    docs = Path("docs")
    if not docs.is_dir():
        return achados
    for doc in sorted(docs.glob("*.md")):
        if doc.name in gen_index.SKIP:
            continue
        for line in doc.read_text(encoding="utf-8").splitlines():
            if gen_index.PATTERN.match(line):
                continue
            m = QUASE.match(line)
            # O token precisa ter LETRA e DIGITO para parecer um ID de registro.
            # So digito nao basta: "## 1. Contexto" e secao narrativa legitima, e
            # exigir apenas digito acusava ela — o que levou alguem a tirar a
            # numeracao de um documento real para calar o aviso. Falso positivo
            # que faz o usuario mutilar o proprio conteudo e pior que nenhum aviso.
            if not m:
                continue
            ident = m.group(1)
            parece_id = re.search(r"[A-Za-z]", ident) and re.search(r"\d", ident)
            if parece_id and m.group(2) not in SEPARADORES:
                achados.setdefault(doc.as_posix(), []).append((line.strip(), m.group(2)))
    return achados


def checar_cabecalhos():
    print("== Cabeçalho que quase casa? ==")
    achados = quase_casando()
    if not achados:
        print("  ok     nenhum cabeçalho parecido com registro ficou de fora")
        return
    for arquivo, linhas in achados.items():
        print("  !!     " + arquivo + ": " + str(len(linhas))
              + " cabeçalho(s) parecem registro e não foram indexados")
        print('         ex.: "' + linhas[0][0][:66] + '"')
        seps = sorted({sep for _, sep in linhas})
        print("         separador encontrado: " + " ".join(seps)
              + "  — esperado: — (travessão), – ou -")


def checar_adocao():
    """A adocao termina quando a estrutura esta portada (AD-01 a AD-03). Escrever
    o estado real e a PRIMEIRA SESSAO DE TRABALHO, nao a adocao — quem acabou de
    adotar nao conhece os papeis dos documentos e nao teria como escrever."""
    print("== Estado do projeto escrito? ==")
    if not HANDOFF.exists():
        print("  --     state/handoff.md ausente — rode 'make init'")
        return
    texto = HANDOFF.read_text(encoding="utf-8")
    modelo = MODELO_HANDOFF.read_text(encoding="utf-8") if MODELO_HANDOFF.exists() else ""
    if modelo and texto.strip() == modelo.strip():
        print("  !!     state/handoff.md ainda é o estado de transição da adoção")
        print("         Ninguém consegue retomar este projeto ainda. Reescreva-o do")
        print("         zero ao fim da primeira sessão de trabalho — é a AD-04 em")
        print("         state/aberto.md. Não é pendência de adoção: é o primeiro")
        print("         fechamento de sessão.")
    elif GERADO_EM.search(texto):
        print("  !!     state/handoff.md sem data de geração — adoção incompleta")
        print("         Preencha o campo. O handoff é datado de propósito: sem data,")
        print("         quem lê não sabe se está diante de estado ou de arquivo velho.")
    else:
        print("  ok     handoff preenchido com o estado do projeto")


def checar_refs():
    """refs/ povoado sem manifesto passa despercebido: a conferencia existe, mas
    e o `make intake`, que so roda se alguem lembrar. O check roda por obrigacao,
    antes de toda acao nova — e ate aqui nunca olhou para refs/.

    Compara so presenca: arquivo sem declaracao, declaracao sem arquivo. A
    conferencia completa continua no intake. NAO reprova, pela mesma razao das
    outras secoes: refs/ povoado antes do manifesto e o estado normal no meio de
    uma adocao, e check vermelho no primeiro dia ensina a ignorar o check."""
    print("== refs/ declarado? ==")
    arquivos = intake.arquivos()
    if not arquivos:
        print("  ok     refs/ vazio ou ausente — nada a declarar")
        return
    decl = intake.declared()
    if decl is None:
        print("  !!     " + str(len(arquivos)) + " arquivo(s) em refs/ e nenhum manifesto")
        print("         Rode 'make intake': ele cria o modelo de refs/_fontes.md.")
        print("         Sem manifesto, ninguém sabe de que serve cada arquivo nem")
        print("         qual ainda vale — e o agente relê tudo para descobrir.")
        return
    conhecidos = intake.exemplos()
    sem_declaracao = [f.name for f in arquivos if f.name not in decl]
    presentes = {f.name for f in arquivos}
    sumidos = [n for n in decl if n not in conhecidos and n not in presentes]
    if not sem_declaracao and not sumidos:
        print("  ok     refs/ e o manifesto batem — " + str(len(arquivos)) + " arquivo(s)")
        return
    if sem_declaracao:
        print("  !!     " + str(len(sem_declaracao)) + " arquivo(s) em refs/ fora do manifesto: "
              + ", ".join(sem_declaracao[:4]) + ("…" if len(sem_declaracao) > 4 else ""))
    if sumidos:
        print("  !!     " + str(len(sumidos)) + " declarado(s) que não estão em refs/: "
              + ", ".join(sumidos[:4]) + ("…" if len(sumidos) > 4 else ""))
    print("         Rode 'make intake' para o detalhe.")


def main():
    print("== Arquivos de método ==")
    faltando = [f for f in ARQUIVOS if not Path(f).exists()]
    for f in ARQUIVOS:
        print(("  ok     " if Path(f).exists() else "  FALTA  ") + f)
    if faltando:
        print("")
        print("  " + str(len(faltando)) + " arquivo(s) faltando — rode 'make init'.")
    print("")
    print("== Índice defasado? ==")
    indice = gen_index.check_index()
    print("")
    checar_cabecalhos()
    print("")
    checar_adocao()
    print("")
    checar_refs()
    print("")
    estado = check_state.check_state()
    # So indice e estado reprovam. Ver o docstring: check vermelho no primeiro
    # dia de adocao ensina a ignorar o check.
    return indice or estado


if __name__ == "__main__":
    sys.exit(main())
