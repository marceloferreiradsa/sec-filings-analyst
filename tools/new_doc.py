#!/usr/bin/env python3
"""Cria um documento canônico novo com cabeçalho de escopo e rodapé de revisão.

O cabeçalho de escopo existe para responder, sem ler o documento inteiro, de que
ele é dono e o que apenas aponta. É a defesa contra o mesmo fato ser escrito em
dois lugares e divergir.
"""
import sys
from datetime import date
from pathlib import Path

# Windows: sem isto, o stdout sai em cp1252 e corrompe os acentos das mensagens.
sys.stdout.reconfigure(encoding="utf-8")

TEMPLATE = """# {title}

> **Escopo:** este documento é dono de TODO. Aponta para TODO em vez de duplicar.

---

## TODO

---
**Última revisão:** {today} · detalhe em `state/changelog.md`
"""


def main():
    if len(sys.argv) < 2:
        print("  uso: make doc DOC=nome_do_documento")
        return 1
    name = sys.argv[1].removesuffix(".md")
    target = Path("docs") / f"{name}.md"
    if target.exists():
        print(f"  já existe: {target}")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    title = name.replace("_", " ").replace("-", " ").capitalize()
    target.write_text(TEMPLATE.format(title=title, today=date.today().isoformat()), encoding="utf-8", newline="\n")
    print(f"  criado: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
