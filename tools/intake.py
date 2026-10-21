#!/usr/bin/env python3
"""Confere refs/ contra o manifesto refs/_fontes.md.

refs/ guarda as especificações feitas pelo cliente, usuário final do produto/serviço
gerado pelo projeto e/ou decididas em conjunto com a área de desenvolvimento — mais
contrato, manual, dicionário de dados, export de planilha. O agente lê, nunca edita.

Dois problemas resolvidos aqui:

1. Documento que o agente não consegue ler no momento certo é documento que não
   existe. PDF e planilha são caros de ler e não entram no índice; markdown entra.
2. Ninguém lembra de que serve cada arquivo, nem qual ainda vale. Parentesco entre
   um original e sua versão derivada NÃO é adivinhável por nome de arquivo — tem de
   ser declarado.

Por isso refs/_fontes.md é escrito a mão e este script apenas CONFERE: arquivo sem
declaração, declaração sem arquivo, e original pesado sem derivado.

Uso: python tools/intake.py
"""
import io
import re
import sys
from pathlib import Path

# Windows: sem isto, o stdout sai em cp1252 e corrompe os acentos das mensagens.
sys.stdout.reconfigure(encoding="utf-8")

REFS = Path("refs")
MANIFEST = REFS / "_fontes.md"
# Documentacao do metodo, nao fonte externa: fica fora do manifesto.
IGNORE = {"README.md"}
HEADING = re.compile(r"^#{1,3}\s+(?![`#])(.+?)\s*$")
# A quarta coluna e opcional: manifesto de tres colunas, escrito antes dela
# existir, continua sendo lido.
ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|([^|]*)\|([^|]*)\|(?:([^|]*)\|)?")

NATIVE = {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".sql"}
HEAVY = {".pdf", ".xlsx", ".xls", ".docx", ".pptx", ".odt"}

TEMPLATE = """# Fontes externas — o que há em `refs/` e de que serve

> **Escrito a mão.** `make intake` confere este manifesto contra os arquivos de
> `refs/`, mas não adivinha parentesco: qual markdown deriva de qual PDF só você sabe.
>
> **Nada em `refs/` é editado pelo agente.** São fontes externas. Se um original
> precisa virar legível, a versão derivada também mora aqui e é declarada abaixo.

| Arquivo | O que é | Derivado em | Origem |
|---|---|---|---|
| `exemplo.pdf` | Especificação do cliente, v2 de 06/05 | `exemplo_indexado.md` | — |
| `exemplo_indexado.md` | Versão indexada do PDF, preservando a paginação | — | — |
| `exemplo_arquivado.xlsx` | Planilha antiga, mantida só por histórico | n/a — não vale derivar | — |
| `exemplo_copiado.md` | Subsídio mantido por outro projeto | — | `../outro-projeto/subsidios/exemplo.md` · cópia de 24/09/2026 |

**Terceira coluna, derivação de formato:** caminho entre crases se há derivado;
`n/a — razao` se a ausência é deliberada; `—` se ainda está pendente.

**Quarta coluna, procedência:** `—` quando o arquivo é fonte externa nativa — o PDF do
cliente, o contrato, o export. Caminho e data quando é **cópia de documento mantido em
outro lugar**. A distinção importa porque correção feita na cópia não volta para o
original, e quem lê precisa saber de qual dos dois está falando.
"""


def declared():
    if not MANIFEST.exists():
        return None
    out = {}
    for l in io.open(MANIFEST, encoding="utf-8"):
        m = ROW.match(l.strip())
        if not m:
            continue
        name, what, derived = (g.strip() if g else "" for g in m.groups()[:3])
        origem = (m.group(4) or "").strip()
        # só o primeiro trecho entre crases conta como caminho; o resto é prosa
        raw = derived.strip()
        mm = re.search(r"`([^`]+)`", raw)
        if mm:
            d = mm.group(1).strip()
        elif raw.lower().startswith(("n/a", "na ", "não se aplica")):
            d = "N/A"          # ausência deliberada, com justificativa na própria célula
        else:
            d = ""
        out[name] = {"what": what, "derived": d or None, "origem": origem or None}
    return out


def arquivos():
    """Os arquivos de refs/ que o manifesto deve declarar.

    Vive aqui, e nao no check.py, para a regra do que conta existir uma vez so:
    duas listagens com criterios que divergem com o tempo dariam respostas
    diferentes sobre o mesmo diretorio."""
    if not REFS.is_dir():
        return []
    return sorted(p for p in REFS.iterdir() if p.is_file()
                  and p.name != MANIFEST.name and p.name not in IGNORE)


def exemplos():
    """Nomes de exemplo do modelo: declarados, mas nao devem existir em refs/."""
    return set(re.findall(r"^\|\s*`([^`]+)`", TEMPLATE, re.M))


def main():
    if not REFS.is_dir():
        print("  refs/ não existe.")
        print("  Crie e coloque ali as especificações: o que o cliente ou o")
        print("  usuário final do produto definiu, contrato, manual, dicionário.")
        print("  manual do cliente, dicionário de dados. Depois rode este comando.")
        return 0

    files = arquivos()
    if not files:
        print("  refs/ está vazio.")
        return 0

    decl = declared()
    if decl is None:
        MANIFEST.write_text(TEMPLATE, encoding="utf-8", newline="\n")
        print("  refs/_fontes.md criado a partir do modelo.")
        print("  Descreva os %d arquivo(s) de refs/ nele e rode de novo." % len(files))
        return 1

    issues = []
    print("== refs/ — %d arquivo(s), manifesto em refs/_fontes.md ==" % len(files))
    for f in files:
        ext = f.suffix.lower()
        d = decl.get(f.name)
        if d is None:
            print("  DECLARAR %-42s ausente do manifesto" % f.name)
            issues.append(f.name)
            continue
        if ext == ".md":
            n = sum(1 for l in io.open(f, encoding="utf-8", errors="replace")
                    if HEADING.match(l))
            print("  ok       %-42s %d cabeçalhos, indexável" % (f.name, n))
        elif ext in NATIVE:
            print("  ok       %-42s legível direto" % f.name)
        elif ext in HEAVY:
            if d["derived"] == "N/A":
                print("  ok       %-42s sem derivado, por decisão declarada" % f.name)
            elif d["derived"]:
                target = REFS / d["derived"]
                if target.exists() or Path(d["derived"]).exists():
                    print("  ok       %-42s derivado: %s" % (f.name, d["derived"]))
                else:
                    print("  QUEBRADO %-42s derivado declarado não existe: %s"
                          % (f.name, d["derived"]))
                    issues.append(f.name)
            else:
                print("  DERIVAR  %-42s caro de ler, sem derivado declarado" % f.name)
                issues.append(f.name)
        else:
            print("  ?        %-42s extensão desconhecida" % f.name)

    # Nomes de exemplo do modelo nao contam como sumidos. Derivados do proprio
    # TEMPLATE para nao ficarem defasados quando o modelo mudar.
    conhecidos = exemplos()
    ghosts = [n for n in decl if n not in conhecidos
              and not (REFS / n).exists() and not Path(n).exists()]
    for n in ghosts:
        print("  SUMIU    %-42s declarado no manifesto, não está em refs/" % n)
        issues.append(n)

    print("")
    if issues:
        print("  %d pendência(s)." % len(issues))
        print("  Para os DERIVAR, peça ao agente: \"converta em markdown indexado,")
        print("  preservando a numeração de seção e a paginação do original\".")
        print("  Depois: registre o derivado em refs/_fontes.md e rode make docs-index")
        return 1
    print("  refs/ íntegro. Rode make docs-index se algum markdown mudou.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
