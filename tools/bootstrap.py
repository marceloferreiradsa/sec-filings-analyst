#!/usr/bin/env python3
"""Converte uma cópia do template em um projeto próprio.

Faz só a parte MECÂNICA: troca o nome, remove os arquivos que são do template
e não do projeto, zera o estado. A parte de JULGAMENTO — o que o projeto e,
quais tipos de mudança ele tem, quais convenções valem — fica para a primeira
conversa com o agente, e o bootstrap deixa o prompt pronto para isso.

Não mexe em git: imprime os comandos para você conferir antes de rodar.
"""
import shutil
import sys
from pathlib import Path

# Windows: sem isto, o stdout sai em cp1252 e corrompe os acentos das mensagens.
sys.stdout.reconfigure(encoding="utf-8")

# --- Valores especificos do idioma. Para uma versao em outro idioma, e so
# --- traduzir este bloco: o resto do script nao tem texto embutido.
PLACEHOLDER = "{NOME DO PROJETO}"
# So o README do template sai. O COMO-ADOTAR viaja junto e e apagado pelo proprio
# guia, no ultimo passo: quem adota nao tem outra copia dele em maos.

NEW_README = """# {name}

{{Uma frase dizendo o que este projeto faz.}}

## Trabalhando neste projeto

O método está em `CLAUDE.md`; o estado atual, em `state/handoff.md`.
`make metodo-help` lista os comandos.

Ao abrir uma sessão com o agente, ele lê `state/handoff.md` e `state/aberto.md`
— não é preciso recontar o histórico.

## O que é método e o que é este projeto

Numa pasta com dez markdowns, a dúvida mais comum é qual deles descreve o projeto.

| Caminho | O que é |
|---|---|
| `CLAUDE.md` · `METODO.md` · `Makefile` · `tools/` · `.template/` | **estrutura do método** — vale para qualquer projeto e não descreve este |
| `state/` | onde este projeto parou, o que ficou pendente, e por que está assim |
| `docs/` | os documentos canônicos **deste** projeto |
| `refs/` | especificação de fora: o agente lê, nunca edita |
| a raiz | o **produto** — o que este projeto entrega |

Ler o método não ensina nada sobre o projeto.
"""

def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print('  uso: make bootstrap NAME="Nome do Projeto"')
        return 1
    name = sys.argv[1].strip()

    claude_md = Path("CLAUDE.md")
    if not claude_md.exists():
        print("  CLAUDE.md não encontrado — está na pasta certa?")
        return 1

    text = claude_md.read_text(encoding="utf-8")
    if PLACEHOLDER not in text:
        print("  Este projeto já passou pelo bootstrap (CLAUDE.md sem placeholder).")
        print("  Nada a fazer — abortando para não sobrescrever seu conteúdo.")
        return 1

    # 1. nome no CLAUDE.md, sem a nota de adoção
    # A nota de adoção NÃO é removida aqui: ela define o papel do agente
    # enquanto houver `{...}` no arquivo, e some quando a adoção termina.
    # Removê-la no bootstrap deixava o projeto novo com marcadores por
    # preencher e nenhuma instrução sobre o que fazer com eles.
    text = text.replace(PLACEHOLDER, name)
    claude_md.write_text(text, encoding="utf-8", newline="\n")
    print(f"  CLAUDE.md  nome definido: {name}")

    # 2. README: escreve só se não houver. No caso B o projeto já tem o dele, e
    # sobrescrever destruiria a porta de entrada de um projeto que existe há meses.
    # No caso A não há README na pasta — o `make novo` não copia o do template.
    if Path("README.md").exists():
        print("  README.md  preservado (já existia)")
    else:
        Path("README.md").write_text(NEW_README.format(name=name),
                                     encoding="utf-8", newline="\n")
        print("  README.md  criado para o projeto")

    # 3. estado zerado
    for source in Path(".template").glob("*.md"):
        target = (Path("docs") if source.name == "_index.md" else Path("state")) / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    print("  state/     zerado a partir dos modelos")

    # O modelo de _index.md nao e o que o gerador produz, entao copiar e parar
    # deixaria o projeto nascendo com `make docs-check` vermelho — na estreia, que e
    # justamente quando um check vermelho ensina a ignorar o check.
    import gen_index
    gen_index.INDEX.write_text(gen_index.render(gen_index.scan()),
                               encoding="utf-8", newline="\n")
    print("  docs/      índice gerado")


    # Sem instrução de próximo passo aqui, de propósito: há dois pontos de
    # entrada — `make novo` e a cópia manual — e o próximo passo é diferente em
    # cada um. Quem chama é que sabe qual imprimir.
    return 0


if __name__ == "__main__":
    sys.exit(main())
