#!/usr/bin/env python3
"""Instala o metodo num projeto que ja existe (o caso B da adocao).

Roda DE DENTRO do clone do template, como o `python -m metodo novo`.

Por que existe: o caso B era um `cp -r` manual, e o `cp` **sobrescreve sem
aviso**. Projeto que ja existe e justamente o que tem `Makefile`, `CLAUDE.md` e
uma pasta `tools/` — num caso real, o Makefile de 250 linhas, com pipeline e
deploy, so nao foi perdido porque o agente olhou o destino antes. E o `cp`
copiava menos que o `novo`: sem `.gitattributes`, o `harness.sh` voltava com
CRLF e o bash nao o rodava. Os dois caminhos de adocao divergiam em silencio, e
o mais usado era o mais pobre. Aqui a lista e a mesma do `novo.py`.

O metodo mora inteiro em `metodo/` e roda por `python -m metodo`, entao **o
Makefile do projeto nao e tocado** — nem lido. A versao anterior acrescentava
um `include` nele, e mesmo isso era o metodo dentro de um arquivo do projeto.

Regra: **nada e sobrescrito.** Antes de escrever qualquer arquivo, confere
todas as colisoes; havendo uma, lista e para. Os tres arquivos que o projeto
quase sempre ja tem recebem tratamento proprio, porque recusar neles seria
recusar a adocao inteira:

- `CLAUDE.md`: o existente vira `CLAUDE.anterior.md` e o do metodo entra. A
  `AD-03` manda mesclar um no outro e apagar o anterior. Nada se perde.
- `.gitattributes`: copiado se nao existir. Se existir, fica como esta — regra
  de atributo depende de ordem, e anexar mudaria o comportamento do projeto.
- `.gitignore`: recebe so as linhas do metodo que faltam.

Arvore suja e arquivo grande fora do git so geram AVISO: o caso B e projeto
vivo, e projeto vivo raramente esta limpo. Mas a adocao deve sair num commit
proprio, e o primeiro `git add -A` e o primeiro que pode publicar lixo grande.

    python -m metodo adotar ../meu-projeto ["Meu Projeto"]
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import novo  # noqa: E402  (reaproveita as listas: um fato, um lugar)

# Tratados a parte, ver o docstring. Nao entram na conferencia de colisao.
ESPECIAIS = {"CLAUDE.md", ".gitattributes", ".gitignore"}
ANTERIOR = "CLAUDE.anterior.md"
OPCIONAL = ".vscode/"
BLOCO_GITIGNORE = "\n# Metodo (ai-project-framework)\n"

# Sinais de que o metodo ja esta no destino: a pasta de hoje, ou o que as
# adocoes anteriores deixavam (antes de existir a pasta `metodo/`).
JA_ADOTADO = [novo.PACOTE, ".template", "metodo.mk"]

# O que o bootstrap vai escrever: se ja existe, o projeto ja tem estado, e
# zerar seria destruir. Recusa como qualquer outra colisao.
ESTADO = ["state/handoff.md", "state/changelog.md", "state/aberto.md", "docs/_index.md"]

GRANDE = 10 * 1024 * 1024


def _git(destino, *args):
    try:
        r = subprocess.run(("git", "-C", str(destino)) + args, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def a_copiar():
    """[(origem, relativo)] de todo arquivo comum do metodo, fora os especiais."""
    itens = []
    for f in novo.ARQUIVOS:
        if f not in ESPECIAIS and Path(f).is_file():
            itens.append((Path(f), f))
    for d in novo.PASTAS:
        for p in sorted(Path(d).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                itens.append((p, p.as_posix()))
    return itens


def linhas_gitignore():
    """Padroes do .gitignore do template, sem os ancorados na raiz (`/...`):
    esses descrevem o repositorio do template, nao o metodo."""
    padroes = []
    for linha in Path(".gitignore").read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        if s and not s.startswith("#") and not s.startswith("/"):
            padroes.append(s)
    return padroes


def fim_de_linha(texto):
    return "\r\n" if "\r\n" in texto else "\n"


def main():
    destino_arg = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    nome = (sys.argv[2] if len(sys.argv) > 2 else "").strip()
    if not destino_arg:
        print('  uso: python -m metodo adotar ../meu-projeto ["Meu Projeto"]')
        print("")
        print("  Instala o método num projeto que já existe, sem sobrescrever nada.")
        print("  Projeto do zero: python -m metodo novo.")
        return 1

    if not Path("CLAUDE.md").exists() or not Path(novo.MODELOS).is_dir():
        print("  Este comando roda de dentro do clone do template.")
        print("  Não encontrei CLAUDE.md e " + novo.MODELOS + "/ aqui.")
        return 1
    if novo.PLACEHOLDER not in Path("CLAUDE.md").read_text(encoding="utf-8"):
        print("  O CLAUDE.md daqui já foi personalizado: esta pasta é um projeto")
        print("  adotado, não o template. Rode de dentro do clone do template.")
        return 1

    destino = Path(destino_arg)
    if not destino.is_dir():
        print("  A pasta não existe: " + str(destino))
        print("  Projeto do zero é o caso A: python -m metodo novo --caminho ...")
        return 1
    if destino.resolve() == Path(".").resolve():
        print("  O destino é o próprio template.")
        return 1
    if not nome:
        nome = novo.humanizar(destino.resolve().name)

    # --- 1. Conferencia completa, antes de escrever qualquer coisa ---
    achados = [s for s in JA_ADOTADO if (destino / s).exists()]
    if achados:
        print("  O destino já tem o método, ou uma pasta com o nome dele: "
              + ", ".join(achados))
        print("  Atualizar um projeto já adotado é propagação, não adoção.")
        if novo.PACOTE in achados and not (destino / novo.MODELOS).is_dir():
            print("  Se '" + novo.PACOTE + "/' é uma pasta do projeto, renomeie-a antes:")
            print("  o método precisa desse nome para rodar por 'python -m metodo'.")
        return 1

    itens = a_copiar()
    # Opcional e comum em projeto existente: o do projeto fica, sem recusar.
    preservados = [rel for _, rel in itens
                   if rel.startswith(OPCIONAL) and (destino / rel).exists()]
    itens = [(o, rel) for o, rel in itens if rel not in preservados]
    colisoes = [rel for origem, rel in itens
                if (destino / rel).exists()
                and (destino / rel).read_bytes() != origem.read_bytes()]
    colisoes += [rel for rel in ESTADO if (destino / rel).exists()]
    if (destino / "CLAUDE.md").exists() and (destino / ANTERIOR).exists():
        colisoes.append(ANTERIOR)
    if colisoes:
        print("  RECUSADO   " + str(len(colisoes)) + " arquivo(s) do destino seriam sobrescritos:")
        for c in colisoes[:15]:
            print("               " + c)
        if len(colisoes) > 15:
            print("               ... e mais " + str(len(colisoes) - 15))
        print("")
        print("  Nada foi escrito. Renomeie ou mova esses arquivos e rode de novo.")
        return 1

    # --- 2. Avisos: nao recusam ---
    status = _git(destino, "status", "--porcelain")
    if status is None:
        print("  AVISO      o destino não é repositório git: a adoção não terá um")
        print("             commit próprio para reverter.")
    elif status.strip():
        n = len(status.strip().splitlines())
        print("  AVISO      " + str(n) + " mudança(s) não commitada(s) no destino.")
        print("             Commite o trabalho pendente À PARTE, antes ou depois:")
        print("             a adoção deve sair num commit próprio e reversível.")
    soltos = _git(destino, "ls-files", "-o", "--exclude-standard") or ""
    grandes = []
    for rel in soltos.splitlines():
        p = destino / rel
        if p.is_file() and p.stat().st_size >= GRANDE:
            grandes.append((rel, p.stat().st_size))
    if grandes:
        print("  AVISO      arquivo(s) grande(s) fora do git e não ignorados — o")
        print("             commit da adoção com `git add -A` os versionaria:")
        for rel, tam in grandes[:8]:
            print("               " + rel + "  (" + str(tam // (1024 * 1024)) + " MB)")

    # --- 3. Escrita ---
    for origem, rel in itens:
        alvo = destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem, alvo)
    print("  copiado    " + str(len(itens)) + " arquivo(s) do método")
    for rel in preservados:
        print("  preservado " + rel + " (já existia; o do método não entrou)")

    claude = destino / "CLAUDE.md"
    if claude.exists():
        claude.rename(destino / ANTERIOR)
        print("  CLAUDE.md  o existente foi preservado em " + ANTERIOR)
        print("             (a AD-03 manda mesclar e apagar)")
    shutil.copyfile("CLAUDE.md", claude)

    attrs = destino / ".gitattributes"
    if attrs.exists():
        print("  .gitattr.  preservado. Confira se ele garante LF para *.sh: sem isso,")
        print("             com autocrlf=true, o bash não roda " + novo.PACOTE + "/harness.sh")
    else:
        shutil.copyfile(".gitattributes", attrs)
        print("  .gitattr.  copiado")

    ignore = destino / ".gitignore"
    existente = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    presentes = {l.strip() for l in existente.splitlines()}
    faltam = [p for p in linhas_gitignore() if p not in presentes]
    if faltam:
        eol = fim_de_linha(existente) if existente else "\n"
        bloco = BLOCO_GITIGNORE + "\n".join(faltam) + "\n"
        if existente and not existente.endswith(("\n", "\r\n")):
            bloco = "\n" + bloco
        if not existente:
            bloco = bloco.lstrip("\n")
        with open(ignore, "a", encoding="utf-8", newline="") as fh:
            fh.write(bloco.replace("\n", eol))
        print("  .gitignore " + str(len(faltam)) + " linha(s) do método acrescentada(s)")
    else:
        print("  .gitignore já cobre o método")

    if (destino / "Makefile").exists():
        print("  Makefile   não tocado: é do projeto")

    # --- 4. Bootstrap, la dentro ---
    # flush obrigatorio: sem ele o buffer do pai solta depois do que o filho ja
    # escreveu direto no terminal, e a saida sai fora de ordem.
    sys.stdout.flush()
    r = subprocess.run([sys.executable, "-m", novo.PACOTE, "bootstrap", nome],
                       cwd=str(destino), encoding="utf-8")
    if r.returncode != 0:
        print("  O bootstrap falhou. Os arquivos do método já foram copiados.")
        return 1

    print("")
    print("  Agora, no projeto:")
    print("    cd " + str(destino))
    print("    python -m metodo check")
    print("    claude")
    print("")
    print("  E peça ao agente: \"leia o " + novo.GUIA + " e me guie na adoção\".")
    print("  Antes do commit da adoção, confira o git status: ela sai num commit só dela.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
