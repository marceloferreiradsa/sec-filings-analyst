#!/usr/bin/env python3
"""Imprime a ajuda do Makefile.

Por que isto nao e um `@echo` no proprio Makefile: `@echo` sai pela codepage do
terminal, que no Windows corrompe acento — `dívida` vira `dÃ­vida`. Nao ha
conserto dentro do Makefile. Aqui, uma linha de reconfigure resolve, e a
primeira tela que alguem ve deixa de ser a unica em portugues capenga.

O alinhamento das colunas e CALCULADO a partir do nome mais longo, e nao
escrito a mao. Alinhamento manual apodrece na primeira vez que alguem acrescenta
um alvo com nome maior — que foi exatamente o que aconteceu com a versao
anterior desta ajuda.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

GRUPOS = [
    ("ESTRUTURA", [
        ("novo", "cria um projeto novo a partir deste template (NOME=... ou CAMINHO=...)"),
        ("release", "gera a árvore limpa do template para o repositório público (DESTINO=...)"),
        ("init", "cria pastas e arquivos de estado (não sobrescreve existentes)"),
        ("bootstrap", "converte uma cópia do template em projeto próprio (NAME=...)"),
        ("check", "verifica o que falta e se o índice está defasado"),
        ("tree", "mostra a estrutura atual"),
        ("test", "roda a bateria de regressão dos geradores"),
    ]),
    ("DOCUMENTAÇÃO", [
        ("index", "regenera docs/_index.md varrendo os canônicos"),
        ("intake", "confere refs/ contra o manifesto refs/_fontes.md"),
        ("adr", "cria a próxima decisão arquitetural a partir do modelo"),
        ("dt", "cria a próxima dívida técnica a partir do modelo"),
        ("doc", "cria documento canônico novo (DOC=nome)"),
    ]),
    ("SESSÃO", [
        ("session", "abre o Claude Code retomando a conversa anterior"),
        ("mcp-list", "lista os servidores MCP configurados"),
    ]),
    ("MANUTENÇÃO", [
        ("clean", "remove temporários (nunca toca em docs/ ou state/)"),
    ]),
]

RODAPE = "Adotando o template agora? O passo a passo está em COMO-ADOTAR.md."


def main():
    largura = max(len(alvo) for _, alvos in GRUPOS for alvo, _ in alvos)
    for grupo, alvos in GRUPOS:
        print(grupo)
        for alvo, descricao in alvos:
            print("  make " + alvo.ljust(largura) + "  " + descricao)
        print("")
    print(RODAPE)


if __name__ == "__main__":
    main()
