#!/usr/bin/env python3
"""Cria o próximo ADR em docs/decisoes_arquiteturais.md.

    python -m metodo adr "Título da decisão"

Lê o maior número existente e incrementa. Numeração nunca é reaproveitada:
um ADR superado muda de status, nunca some — a data histórica preserva a
rastreabilidade de por que a decisão foi tomada com o que se sabia na época.

O título vem do argumento. Sem argumento, de um terminal (pergunta) ou de um
pipe (primeira linha). Sem título, sai sem gravar nada: quem roda isto de um
agente, sem terminal, não pode ficar esperando uma pergunta que ninguém vê.
"""
import re
from datetime import date
import sys
from pathlib import Path

# Windows: sem isto, o stdout sai em cp1252 e corrompe os acentos das mensagens.
sys.stdout.reconfigure(encoding="utf-8")

# Nome de arquivo especifico do idioma: traduzir numa versao em outro idioma.
DOC = Path("docs/decisoes_arquiteturais.md")

TEMPLATE = """
<a id="adr-{n:02d}"></a>

## ADR-{n:02d} — {title}

**Status:** Pendente

**Contexto:** o que estava em jogo e por que uma decisão era necessária.

**Decisão:** o que foi decidido, no imperativo.

**Alternativas consideradas:** o que foi descartado e **por que**. Esta seção é a
que dá valor ao ADR meses depois — sem ela, ninguém sabe se a alternativa óbvia
já foi pensada.

**Consequências:** o que passa a ser verdade, incluindo o que piora. Se a decisão
tem custo, ele fica aqui.

*Registrado em {today}.*

---
"""


def ler_titulo(pergunta):
    """Título do argumento, do terminal ou do pipe. None se não houver."""
    if sys.argv[1:]:
        return " ".join(sys.argv[1:]).strip() or None
    if sys.stdin is None:
        return None
    if sys.stdin.isatty():
        try:
            return input(pergunta).strip() or None
        except EOFError:
            return None
    # Pipe: no Windows chega em cp1252 se não reconfigurar, e o acento corrompe.
    sys.stdin.reconfigure(encoding="utf-8")
    return sys.stdin.readline().strip() or None


def sem_titulo(comando):
    print("  Sem título: nada gravado.")
    print('  uso: python -m metodo ' + comando + ' "Título"')
    return 1


def proximo(texto, prefixo):
    numeros = [int(m) for m in re.findall(r"^## " + prefixo + r"-(\d+)", texto, re.M)]
    return max(numeros) + 1 if numeros else 1


def main():
    # O título vem antes de criar qualquer arquivo: sem ele, nada se grava.
    n = proximo(DOC.read_text(encoding="utf-8") if DOC.exists() else "", "ADR")
    title = ler_titulo(f"Título do ADR-{n:02d}: ")
    if not title:
        return sem_titulo("adr")
    if not DOC.exists():
        DOC.parent.mkdir(parents=True, exist_ok=True)
        DOC.write_text(
            "# Decisões Arquiteturais\n\n"
            "> Registro consolidado de decisões. Formato: Contexto -> Decisão ->\n"
            "> Alternativas consideradas -> Consequências.\n>\n"
            "> **Status:** Pendente · Ativa · Ativa mas em reavaliação · Superada\n>\n"
            "> Status é rótulo curto, em texto puro. Ele sobe para `docs/_index.md`\n"
            "> e é o que faz o protocolo parar diante de decisão já tomada — glifo\n"
            "> não atravessa conversão, e não se procura por ele. Comentário vai\n"
            "> depois de um ponto; o índice descarta dali para a frente.\n\n---\n",
            encoding="utf-8", newline="\n",
        )
    text = DOC.read_text(encoding="utf-8")
    DOC.write_text(text.rstrip() + "\n" + TEMPLATE.format(n=n, title=title, today=date.today().isoformat()), encoding="utf-8", newline="\n")
    print(f"  ADR-{n:02d} criado em {DOC}")
    print("  Não esqueça: python -m metodo index")


if __name__ == "__main__":
    sys.exit(main())
