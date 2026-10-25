#!/usr/bin/env python3
"""Leva um projeto ja adotado para a versao do metodo deste template.

Roda DE DENTRO do clone do template, como o `adotar`.

    python -m metodo atualizar ../meu-projeto              # aplica
    python -m metodo atualizar ../meu-projeto --simular    # so mostra o plano

Por que existe: o metodo e copiado, nao instalado, e por isso nao se propaga.
O `adotar` recusa quem ja tem o metodo, e com razao — as regras sao outras. Na
adocao nada se sobrescreve; aqui, o que e do metodo SE SOBRESCREVE, porque a
versao nova e a correta, e o que protege o projeto e o git: a arvore precisa
estar limpa, e tudo o que esta funcao faz se desfaz com um checkout.

Formas que ele reconhece no destino:
- a de hoje: pasta `metodo/` — so troca o conteudo dela;
- as antigas, de antes da pasta: `tools/` com os scripts do metodo, `.template/`,
  `METODO.md` e `VERSAO` na raiz, e alvos de make — o Makefile inteiro do
  template, ou um `metodo.mk` incluido no fim do Makefile do projeto.

**Alvo do metodo se reconhece pelo que ele executa, nunca pelo nome.** Nos
projetos reais o mesmo nome significa coisas diferentes: `make index` e o
indice do metodo num projeto e o FAISS no outro, onde o do metodo se chama
`docs-index`. Quem roda `python tools/gen_index.py --write` e o `index` do
metodo, chame-se ele como for; quem nao roda nada de `tools/` e do projeto, e
nao e tocado nem citado.

Nunca toca em `state/` e `docs/`, com uma excecao: acrescenta ao
`state/aberto.md` o que a versao nova tem e ele nao tem, e as pendencias desta
atualizacao (prefixo `AT-`). O que exige julgamento — texto novo do metodo a
mesclar no `CLAUDE.md`, citacoes em documentos do projeto — vira pendencia, nao
reescrita.
"""
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import adotar  # noqa: E402  (mesclagem de .gitignore e .gitattributes)
import novo    # noqa: E402

# Script antigo -> comando novo. "" e a ajuda (`python -m metodo` sem argumento).
SCRIPTS = {"help.py": "", "novo.py": "novo", "release.py": "release",
           "bootstrap.py": "bootstrap", "check.py": "check", "intake.py": "intake",
           "harness.sh": "test", "gen_index.py": "index", "new_adr.py": "adr",
           "new_dt.py": "dt", "new_doc.py": "doc", "adotar.py": "adotar",
           "check_state.py": None}
# Alvos de conveniencia que existiam e foram cortados: reconhecidos pela receita.
CORTADOS = [("claude --continue", "session"),
            ("-not -path './.template/*'", "tree"),
            ("cache removido", "clean"), ("cache do metodo removido", "clean")]

ANTIGOS_RAIZ = ["metodo.mk", "METODO.md", "VERSAO"]
MODELOS_ANTIGOS = [".template/" + n for n in ("_index.md", "aberto.md", "changelog.md", "handoff.md")]
# Arquivos de metodo que vivem fora da pasta e sao do metodo: sobrescrevem.
DO_METODO_FORA = ["refs/README.md", "mcp/README.md", ".mcp.json.example"]
MODELO_CLAUDE = novo.PACOTE + "/CLAUDE.modelo.md"

ALVO = re.compile(r"^([A-Za-z][\w.-]*)\s*:(?!=)")
INCLUDE = re.compile(r"^\s*-?include\s+metodo\.mk\s*$")
SECAO_SUSPEITAS = "## Suspeitas a verificar"
SECAO_AT = "## Atualização do método"


def _git(destino, *args):
    try:
        r = subprocess.run(("git", "-C", str(destino)) + args, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def alvos(texto):
    """{alvo: receita} de um Makefile. Parser minimo: alvo na coluna 0, receita
    nas linhas com tab logo abaixo. Basta para os Makefiles que o metodo gerou."""
    achados, atual = {}, None
    for linha in texto.splitlines():
        m = ALVO.match(linha)
        if m and not linha.startswith(".") :
            atual = m.group(1)
            achados[atual] = ""
        elif atual and linha.startswith("\t"):
            achados[atual] += linha + "\n"
        elif linha.strip() and not linha.startswith("#"):
            atual = None
    return achados


def classificar(receita):
    """('metodo', comando novo) · ('cortado', nome) · ('projeto', None)."""
    m = re.search(r"tools/([\w.]+\.(?:py|sh))", receita)
    if m and m.group(1) in SCRIPTS:
        return ("metodo", SCRIPTS[m.group(1)])
    if ".template/" in receita and "basename" in receita:
        return ("metodo", "init")
    if ".mcp.json" in receita:
        return ("metodo", "mcp-list")
    for sinal, nome in CORTADOS:
        if sinal in receita:
            return ("cortado", nome)
    return ("projeto", None)


def comando(novo_cmd):
    return "python -m metodo" + (" " + novo_cmd if novo_cmd else "")


class Plano:
    """Lista de acoes. No --simular so se imprime; senao, se imprime e aplica."""

    def __init__(self, destino, simular):
        self.destino, self.simular = destino, simular
        self.pendencias = []

    def fazer(self, rotulo, descricao, acao=None):
        print("  " + rotulo.ljust(10) + " " + descricao)
        if acao and not self.simular:
            acao()


def plano_makefile(plano, mapa):
    """Tira o metodo do Makefile do projeto, ou o Makefile inteiro se ele era do
    template. Devolve nada; registra acao ou pendencia."""
    destino = plano.destino
    make = destino / "Makefile"
    if not make.exists():
        return
    bruto = make.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in bruto else "\n"
    linhas = bruto.splitlines()
    proprios = alvos(bruto)
    do_metodo = [a for a, r in proprios.items() if classificar(r)[0] != "projeto"]

    idx = next((i for i, l in enumerate(linhas) if INCLUDE.match(l)), None)
    if idx is not None:
        # O bloco de comentario logo acima do include sai junto, se falar do metodo.
        ini = idx
        while ini > 0 and linhas[ini - 1].lstrip().startswith("#"):
            ini -= 1
        bloco = linhas[ini:idx]
        if not any(re.search(r"m[eé]todo|framework", l, re.I) for l in bloco):
            ini = idx
        restantes = linhas[:ini] + linhas[idx + 1:]
        while restantes and not restantes[-1].strip():
            restantes.pop()
        if not alvos("\n".join(restantes)):
            plano.fazer("Makefile", "apagado: só incluía o método",
                        lambda: make.unlink())
        else:
            novo_txt = eol.join(restantes) + eol
            plano.fazer("Makefile", "linha 'include metodo.mk' removida ("
                        + str(idx - ini + 1) + " linha(s)); o resto é do projeto",
                        lambda: make.write_bytes(novo_txt.encode("utf-8")))
        return

    if not do_metodo:
        return
    if len(do_metodo) == len(proprios):
        plano.fazer("Makefile", "apagado: era o do template (" + str(len(proprios))
                    + " alvos, todos do método)", lambda: make.unlink())
    else:
        projeto = [a for a in proprios if a not in do_metodo]
        plano.fazer("Makefile", "NÃO tocado: mistura alvos do método e do projeto")
        plano.pendencias.append((
            "Tirar os alvos do método do `Makefile`",
            "Ele mistura alvos do método ("
            + ", ".join("`" + a + "`" for a in do_metodo) + ") com os do projeto ("
            + ", ".join("`" + a + "`" for a in projeto[:6])
            + "), e a separação exige julgamento. Os do método não funcionam mais: os "
            "scripts saíram de `tools/`."))


def reescrever_claude(plano, mapa):
    claude = plano.destino / "CLAUDE.md"
    if not claude.exists():
        return
    bruto = claude.read_bytes()
    texto = bruto.decode("utf-8")
    novos = {a: c for a, (tipo, c) in mapa.items() if tipo == "metodo"}
    cortados = {a: c for a, (tipo, c) in mapa.items() if tipo == "cortado"}
    contagem = 0
    if novos:
        rx = re.compile(r"\bmake (" + "|".join(sorted(map(re.escape, novos), key=len, reverse=True))
                        + r")(?![\w-])")
        contagem = len(rx.findall(texto))
        texto = rx.sub(lambda m: comando(novos[m.group(1)]), texto)
    # Caminhos dos scripts e modelos antigos, so pelos nomes que o metodo conhece:
    # uma pasta `tools/` do projeto pode ser citada no mesmo arquivo.
    rx_tools = re.compile(r"(?<![\w/.-])tools/(" + "|".join(map(re.escape, SCRIPTS)) + r")")
    caminhos = len(rx_tools.findall(texto)) + texto.count(".template/")
    texto = rx_tools.sub(lambda m: novo.PACOTE + "/" + m.group(1), texto)
    texto = re.sub(r"(?<![\w/-])\.template/", novo.MODELOS + "/", texto)
    texto = re.sub(r"(?<![\w/`-])`METODO\.md`", "`" + novo.PACOTE + "/METODO.md`", texto)
    depois = texto.encode("utf-8")
    if depois != bruto:
        if depois.count(b"\n") != bruto.count(b"\n") or depois.count(b"\r") != bruto.count(b"\r"):
            print("  FALHA      CLAUDE.md: a reescrita mudaria o número de linhas. Não gravado.")
            return
        plano.fazer("CLAUDE.md", str(contagem) + " citação(ões) de alvo e " + str(caminhos)
                    + " caminho(s) reescritos", lambda: claude.write_bytes(depois))
    restos = sorted({a for a in cortados if re.search(r"\bmake " + re.escape(a) + r"(?![\w-])", texto)})
    if restos:
        plano.pendencias.append((
            "Citações a comandos que deixaram de existir, no `CLAUDE.md`",
            ", ".join("`make " + a + "` (era o `" + cortados[a] + "`)" for a in restos)
            + ". Apagar ou trocar pelo equivalente direto."))


def citacoes_fora(plano, mapa):
    """Documentos do projeto que citam alvo do metodo: aponta, nao reescreve."""
    nomes = [a for a, (tipo, _) in mapa.items() if tipo != "projeto"]
    if not nomes:
        return
    rx = re.compile(r"\bmake (" + "|".join(map(re.escape, nomes)) + r")(?![\w-])")
    achados, citados = [], set()
    candidatos = [plano.destino / "README.md"] + sorted((plano.destino / "docs").glob("*.md"))
    for p in candidatos:
        if p.is_file() and p.name != "_index.md":
            encontrados = rx.findall(p.read_text(encoding="utf-8", errors="replace"))
            citados.update(encontrados)
            n = len(encontrados)
            if n:
                achados.append(p.relative_to(plano.destino).as_posix() + " (" + str(n) + ")")
    if achados:
        plano.pendencias.append((
            "Citações a alvos antigos do método em documentos do projeto",
            ", ".join(achados) + ". Não foram reescritas, porque o texto é do projeto. "
            "Trocar por `python -m metodo …`. Equivalência: "
            + ", ".join("`make " + a + "` → `" + comando(c) + "`"
                        for a, (t, c) in sorted(mapa.items())
                        if t == "metodo" and a in citados) + "."))


def secoes_novas_claude(plano):
    """Secoes `## ` do metodo que o CLAUDE.md do projeto ainda nao tem."""
    claude = plano.destino / "CLAUDE.md"
    if not claude.exists():
        return
    rx = re.compile(r"^## (.+?)\s*$", re.M)
    meu = set(rx.findall(claude.read_text(encoding="utf-8")))
    faltam = [s for s in rx.findall(Path("CLAUDE.md").read_text(encoding="utf-8"))
              if s not in meu and "{" not in s]
    if faltam:
        plano.pendencias.append((
            "Mesclar no `CLAUDE.md` as seções novas do método",
            ", ".join("*" + s + "*" for s in faltam) + ". O texto está em `"
            + MODELO_CLAUDE + "`, que é o `CLAUDE.md` desta versão do método, sem o projeto. "
            "Comparar também as seções que existem nos dois: o método pode ter mudado "
            "dentro delas."))


def complementar_aberto(plano, origem_v, destino_v):
    aberto = plano.destino / "state" / "aberto.md"
    if not aberto.exists():
        print("  AVISO      state/aberto.md ausente: as pendências abaixo só saem aqui.")
        return
    texto = aberto.read_text(encoding="utf-8")
    acrescimo = ""
    if SECAO_SUSPEITAS not in texto:
        modelo = (Path(novo.MODELOS) / "aberto.md").read_text(encoding="utf-8")
        ini = modelo.find(SECAO_SUSPEITAS)
        fim = modelo.find("\n---", ini)
        if ini >= 0:
            acrescimo += "\n---\n\n" + modelo[ini:fim if fim > 0 else None].rstrip() + "\n"
            plano.fazer("aberto.md", "seção *Suspeitas a verificar* acrescentada")
    # Pendencia que ja foi aberta numa atualizacao anterior nao se repete — aberta
    # ou riscada: riscada quer dizer que alguem ja decidiu sobre ela.
    novas = [(t, c) for t, c in plano.pendencias if " — " + t + "**" not in texto
             and " — " + t + "~~**" not in texto]
    plano.pendencias = novas
    if plano.pendencias:
        n = len(re.findall(r"^\*\*~*AT-\d+", texto, re.M))
        itens = ""
        for i, (titulo, corpo) in enumerate(plano.pendencias, start=n + 1):
            itens += ("\n**AT-" + str(i).zfill(2) + " — " + titulo
                      + "**\n" + corpo + "\n*aberta na atualização de "
                      + date.today().isoformat() + " (" + origem_v + " → " + destino_v + ")*\n")
        if SECAO_AT not in texto:
            acrescimo += ("\n---\n\n" + SECAO_AT + "\n\n> Pendências que a atualização do método "
                          "deixou, com prefixo `AT-`. Riscar conforme feitas.\n")
        acrescimo += itens
        plano.fazer("aberto.md", str(len(plano.pendencias)) + " pendência(s) AT- acrescentada(s)")
    if acrescimo and not plano.simular:
        eol = "\r\n" if "\r\n" in aberto.read_bytes().decode("utf-8") else "\n"
        with open(aberto, "a", encoding="utf-8", newline="") as fh:
            fh.write(acrescimo.replace("\n", eol))


def versao(arquivo):
    if not arquivo.exists():
        return "versão desconhecida"
    linhas = arquivo.read_text(encoding="utf-8").splitlines()
    m = re.search(r"commit (\w+)", " ".join(linhas[:2]))
    return m.group(1) if m else "versão desconhecida"


def main():
    args = [a for a in sys.argv[1:] if a != "--simular"]
    simular = "--simular" in sys.argv[1:]
    destino_arg = (args[0] if args else "").strip()
    if not destino_arg:
        print("  uso: python -m metodo atualizar ../meu-projeto [--simular]")
        print("")
        print("  Leva um projeto já adotado para a versão do método deste template.")
        print("  --simular mostra o plano sem gravar nada.")
        return 1
    if not Path("CLAUDE.md").exists() or not Path(novo.MODELOS).is_dir() \
            or novo.PLACEHOLDER not in Path("CLAUDE.md").read_text(encoding="utf-8"):
        print("  Este comando roda de dentro do clone do template.")
        return 1

    destino = Path(destino_arg)
    if not destino.is_dir() or destino.resolve() == Path(".").resolve():
        print("  Destino inválido: " + str(destino))
        return 1
    pacote = destino / novo.PACOTE
    forma_nova = (pacote / "__main__.py").exists()
    forma_antiga = any((destino / p).exists() for p in ("tools/check.py", ".template", "metodo.mk"))
    if pacote.exists() and not forma_nova:
        print("  O destino tem uma pasta '" + novo.PACOTE + "/' que não é o método.")
        print("  Renomeie-a antes: o método precisa desse nome.")
        return 1
    if not forma_nova and not forma_antiga:
        print("  O destino não tem o método. Para instalar: python -m metodo adotar.")
        return 1

    status = _git(destino, "status", "--porcelain")
    if status is None:
        print("  RECUSADO   o destino não é repositório git. A atualização sobrescreve o")
        print("             que é do método, e o git é o que permite desfazer.")
        return 1
    if status.strip():
        n = len(status.strip().splitlines())
        if not simular:
            print("  RECUSADO   " + str(n) + " mudança(s) não commitada(s) no destino. Commite")
            print("             antes: a atualização sai num commit próprio e reversível.")
            print("             (--simular mostra o plano mesmo assim)")
            return 1
        print("  AVISO      " + str(n) + " mudança(s) não commitada(s): para aplicar, commite antes.")

    origem_v = versao(pacote / "VERSAO") if forma_nova else versao(destino / "VERSAO")
    destino_v = versao(Path(novo.VERSAO)) if Path(novo.VERSAO).exists() else "repositório de desenvolvimento"
    print("  " + ("SIMULAÇÃO  nada será gravado" if simular else "ATUALIZANDO"))
    print("  versão     " + origem_v + " → " + destino_v)
    print("  forma      " + ("pasta metodo/" if forma_nova else "antiga (tools/, .template/, make)"))
    plano = Plano(destino, simular)

    # Mapa dos alvos antigos, pelo que executam. Vem do metodo.mk e do Makefile.
    mapa = {}
    for nome in ("metodo.mk", "Makefile"):
        f = destino / nome
        if f.exists():
            for alvo, receita in alvos(f.read_text(encoding="utf-8", errors="replace")).items():
                tipo, cmd = classificar(receita)
                if tipo != "projeto":
                    mapa[alvo] = (tipo, cmd)
    if mapa:
        print("  alvos      " + ", ".join(
            a + "→" + (comando(c) if t == "metodo" else "cortado") for a, (t, c) in sorted(mapa.items())))

    # --- O que sai ---
    plano_makefile(plano, mapa)
    for rel in ANTIGOS_RAIZ + MODELOS_ANTIGOS:
        p = destino / rel
        if p.is_file():
            plano.fazer("removido", rel, p.unlink)
    for nome in SCRIPTS:
        p = destino / "tools" / nome
        if p.is_file():
            plano.fazer("removido", "tools/" + nome, p.unlink)

    def limpar_pastas():
        for d in ("tools/__pycache__",):
            shutil.rmtree(destino / d, ignore_errors=True)
        for d in ("tools", ".template"):
            p = destino / d
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
    if (destino / "tools").is_dir() or (destino / ".template").is_dir():
        plano.fazer("pastas", "tools/ e .template/ removidas se ficarem vazias", limpar_pastas)

    # --- O que entra ---
    fonte = Path(novo.PACOTE)
    arquivos = [p for p in sorted(fonte.rglob("*"))
                if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]

    def copiar_pacote():
        if forma_nova:
            relativos = {p.relative_to(fonte) for p in arquivos}
            for p in sorted(pacote.rglob("*")):
                if p.is_file() and p.relative_to(pacote) not in relativos \
                        and p.relative_to(pacote).as_posix() != "CLAUDE.modelo.md":
                    p.unlink()
            shutil.rmtree(pacote / "__pycache__", ignore_errors=True)
        for p in arquivos:
            alvo = destino / p
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, alvo)
        shutil.copyfile("CLAUDE.md", destino / MODELO_CLAUDE)
    plano.fazer("metodo/", str(len(arquivos)) + " arquivo(s), mais " + MODELO_CLAUDE
                + " (o CLAUDE.md do método, para mesclar)", copiar_pacote)
    for rel in DO_METODO_FORA + ([novo.GUIA] if (destino / novo.GUIA).exists() else []):
        if Path(rel).is_file():
            alvo = destino / rel
            if not alvo.exists() or alvo.read_bytes() != Path(rel).read_bytes():
                plano.fazer("copiado", rel, lambda r=rel, a=alvo: (
                    a.parent.mkdir(parents=True, exist_ok=True), shutil.copyfile(r, a)))

    ignore = destino / ".gitignore"
    existente = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    faltam = [p for p in adotar.linhas_gitignore()
              if p not in {l.strip() for l in existente.splitlines()}]
    if faltam:
        def mesclar():
            eol = adotar.fim_de_linha(existente) if existente else "\n"
            bloco = adotar.BLOCO_GITIGNORE + "\n".join(faltam) + "\n"
            if existente and not existente.endswith(("\n", "\r\n")):
                bloco = "\n" + bloco
            with open(ignore, "a", encoding="utf-8", newline="") as fh:
                fh.write(bloco.lstrip("\n") if not existente else bloco.replace("\n", eol))
        plano.fazer(".gitignore", str(len(faltam)) + " linha(s) do método acrescentada(s)", mesclar)
    if not (destino / ".gitattributes").exists():
        plano.fazer(".gitattr.", "copiado", lambda: shutil.copyfile(".gitattributes",
                                                                   destino / ".gitattributes"))

    # --- Texto: reescrita mecanica no CLAUDE.md; o resto vira pendencia ---
    reescrever_claude(plano, mapa)
    citacoes_fora(plano, mapa)
    secoes_novas_claude(plano)
    plano.pendencias.append((
        "Registrar no `state/changelog.md` a atualização " + origem_v + " → " + destino_v,
        "Versão do método: " + origem_v + " → "
        + destino_v + ". Anotar o que ela removeu e acrescentou (a saída do `python -m metodo "
        "atualizar`). Depois, `python -m metodo check`."))
    complementar_aberto(plano, origem_v, destino_v)

    # O indice e derivado, e o cabecalho dele cita o comando que o gera: regerar
    # e mecanico, e deixar para depois faria o primeiro check sair vermelho.
    def reindexar():
        subprocess.run([sys.executable, "-m", novo.PACOTE, "index"], cwd=str(destino),
                       capture_output=True, encoding="utf-8")
    if (destino / "docs").is_dir():
        plano.fazer("índice", "docs/_index.md regenerado pela versão nova", reindexar)

    print("")
    if simular:
        print("  Nada foi gravado. Sem --simular, com a árvore limpa, aplica o plano acima.")
        return 0
    print("  Agora, no projeto: git status e git diff para conferir; as pendências AT-")
    print("  estão em state/aberto.md. A atualização sai num commit só dela.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
