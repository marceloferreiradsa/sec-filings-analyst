#!/usr/bin/env python3
"""Gera a arvore limpa do template para o repositorio publico.

Por que existe: **nao se desenvolve um framework por dentro dele.** Este
repositorio e o *projeto que desenvolve* o template — tem `state/` com o
historico das decisoes, `docs/` com os canonicos dele, e pendencias proprias.
Quem clonasse isso receberia mil linhas de changelog do nosso trabalho e um
handoff falando das nossas pendencias, e o agente dele concluiria que esta
trabalhando no template.

A separacao e a mesma que todo framework tem entre **repositorio** e **pacote**:
o que se distribui e gerado, nunca mantido a mao. Aqui o gerado e uma arvore com
o metodo e nada mais — sem `state/`, sem `docs/`, sem historico. Um clone dela e
inconfundivelmente um template.

    python -m metodo release ../ai-project-framework

Escreve por cima do destino sem tocar no `.git` dele, e lista o que sobrou la e
nao faz mais parte do release — arquivo removido daqui precisa ser removido la, e
sem esse aviso ele ficaria no publico para sempre.

O `VERSAO` gravado no destino registra de qual commit daqui aquela copia saiu. E
a unica coisa que torna a propagacao conferivel: quem adotou consegue dizer qual
versao tem.
"""
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import novo  # noqa: E402  (reaproveita as listas: um fato, um lugar)

# O README do template entra no release e nao no `python -m metodo novo`: la o bootstrap
# escreve um README do projeto; aqui ele e a porta de entrada de quem clona.
ARQUIVOS = novo.ARQUIVOS + ["README.md"]
PASTAS = novo.PASTAS

VERSAO = novo.VERSAO
IGNORAR = {".git", ".harness-out", "__pycache__"}


def _git(*args):
    try:
        r = subprocess.run(("git",) + args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def presentes(raiz):
    """Caminhos relativos de tudo que ha no destino, fora o que se ignora."""
    achados = set()
    for p in raiz.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(raiz)
        if IGNORAR & set(rel.parts):
            continue
        achados.add(rel.as_posix())
    return achados


def main():
    destino_arg = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not destino_arg:
        print('  uso: python -m metodo release "../ai-project-framework"')
        print("")
        print("  Gera a árvore limpa do template no destino, sem tocar no .git dele.")
        return 1

    if not Path("CLAUDE.md").exists() or not Path(novo.MODELOS).is_dir():
        print("  Este comando roda de dentro do repositório do template.")
        return 1
    if novo.PLACEHOLDER not in Path("CLAUDE.md").read_text(encoding="utf-8"):
        print("  O CLAUDE.md daqui já foi personalizado: esta pasta é um projeto")
        print("  adotado, não o repositório do template.")
        return 1

    destino = Path(destino_arg)
    destino.mkdir(parents=True, exist_ok=True)
    antes = presentes(destino)

    escritos = set()
    for f in ARQUIVOS:
        if Path(f).exists():
            shutil.copyfile(f, destino / f)
            escritos.add(f)
    for d in PASTAS:
        origem = Path(d)
        if not origem.is_dir():
            continue
        shutil.copytree(origem, destino / d, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for p in origem.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                escritos.add(p.as_posix())

    sha = _git("rev-parse", "--short", "HEAD") or "sem git"
    (destino / VERSAO).write_text(
        "template gerado em " + date.today().isoformat() + "\n"
        "origem: commit " + sha + " do repositório de desenvolvimento\n\n"
        "Este arquivo existe para a propagação ser conferível: quem adotou\n"
        "consegue dizer qual versão tem, e comparar com a atual.\n",
        encoding="utf-8", newline="\n")
    escritos.add(VERSAO)

    print("  gerado     " + str(len(escritos)) + " arquivo(s) em " + str(destino))
    print("  sem        state/ · docs/ · histórico — é um template, não um projeto")

    sobra = sorted(antes - escritos)
    if sobra:
        print("")
        print("  SOBRA      " + str(len(sobra)) + " arquivo(s) no destino que não fazem")
        print("             mais parte do release. Apague-os, ou eles ficam no público")
        print("             para sempre:")
        for s in sobra[:12]:
            print("               " + s)
        if len(sobra) > 12:
            print("               ... e mais " + str(len(sobra) - 12))

    print("")
    print("  Agora, no destino:")
    print("    cd " + str(destino))
    print("    git add -A && git commit -m \"template " + sha + "\"")
    print("    git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
