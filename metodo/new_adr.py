#!/usr/bin/env python3
"""Cria o próximo ADR em docs/decisoes_arquiteturais.md.

Lê o maior número existente e incrementa. Numeração nunca é reaproveitada:
um ADR superado muda de status, nunca some — a data histórica preserva a
rastreabilidade de por que a decisão foi tomada com o que se sabia na época.
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


def main():
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
    numbers = [int(m) for m in re.findall(r"^## ADR-(\d+)", text, re.M)]
    n = max(numbers) + 1 if numbers else 1
    title = input(f"Título do ADR-{n:02d}: ").strip() or "TODO"
    DOC.write_text(text.rstrip() + "\n" + TEMPLATE.format(n=n, title=title, today=date.today().isoformat()), encoding="utf-8", newline="\n")
    print(f"  ADR-{n:02d} criado em {DOC}")
    print("  Não esqueça: python -m metodo index")


if __name__ == "__main__":
    main()
