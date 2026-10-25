#!/usr/bin/env python3
"""Ponto de entrada do metodo: `python -m metodo <comando>`.

Por que nao e Makefile: o metodo e hospede, e quase todo projeto ja tem um
Makefile proprio. Nomes como `index`, `check`, `clean` e `test` colidiam e
faziam outra coisa sem erro nenhum — num caso real, `make clean` apagava
embeddings e `make check` subia um container. O prefixo `metodo-*` resolveu os
nomes, mas o metodo continuava dentro do Makefile do projeto, por uma linha de
`include`, e dependente do GNU make. Aqui ele nao encosta em Makefile nenhum: so
precisa do Python, que os scripts ja exigiam, e roda igual em qualquer shell.

Roda da raiz do projeto. Cada comando chama o `main()` de um script desta pasta
e repassa o codigo de saida — o `check` continua reprovando de verdade.

O alinhamento das colunas da ajuda e CALCULADO a partir do nome mais longo, e
nao escrito a mao: alinhamento manual apodrece no primeiro comando novo.
"""
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Os scripts importam uns aos outros pelo nome curto (`import gen_index`), que e
# o que funciona quando um deles roda direto, como faz a bateria. Com `-m`, a
# pasta do script nao entra sozinha no sys.path.
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

ENTRADA = "python -m metodo"

GRUPOS = [
    ("ESTRUTURA", [
        ("novo", "NOME [--caminho C]", "cria um projeto novo a partir deste template"),
        ("adotar", "DESTINO [NOME]", "instala o método num projeto que já existe"),
        ("atualizar", "DESTINO [--simular]", "leva um projeto já adotado para esta versão"),
        ("release", "DESTINO", "gera a árvore limpa do template para o repositório público"),
        ("init", "", "cria pastas e arquivos de estado (não sobrescreve existentes)"),
        ("bootstrap", "NOME", "converte uma cópia do template em projeto próprio"),
        ("check", "", "verifica o que falta e se o índice está defasado"),
        ("test", "", "roda a bateria de regressão dos geradores"),
    ]),
    ("DOCUMENTAÇÃO", [
        ("index", "", "regenera docs/_index.md varrendo os canônicos"),
        ("intake", "", "confere refs/ contra o manifesto refs/_fontes.md"),
        ("adr", '"TÍTULO"', "cria a próxima decisão arquitetural a partir do modelo"),
        ("dt", '"TÍTULO"', "cria a próxima dívida técnica a partir do modelo"),
        ("doc", "NOME", "cria documento canônico novo"),
    ]),
    ("SESSÃO", [
        ("mcp-list", "", "lista os servidores MCP configurados"),
    ]),
]

RODAPE = ("O Makefile do projeto é do projeto: o método não usa make.\n"
          "Adotando o template agora? O passo a passo está em COMO-ADOTAR.md.")

# Arquivos de estado que o `init` cria a partir dos modelos, se faltarem.
ESTADO = ["state/handoff.md", "state/changelog.md", "state/aberto.md", "docs/_index.md"]
MODELOS = AQUI / "modelos"


def ajuda():
    linhas = [(cmd + (" " + args if args else ""), desc)
              for _, cmds in GRUPOS for cmd, args, desc in cmds]
    largura = max(len(uso) for uso, _ in linhas)
    for grupo, cmds in GRUPOS:
        print(grupo)
        for cmd, args, desc in cmds:
            uso = cmd + (" " + args if args else "")
            print("  " + ENTRADA + " " + uso.ljust(largura) + "  " + desc)
        print("")
    print(RODAPE)
    return 0


def rodar(modulo, *argv):
    """Chama o main() do script como se ele tivesse sido rodado direto."""
    mod = importlib.import_module(modulo)
    sys.argv = [modulo + ".py", *argv]
    return mod.main() or 0


def init(_args):
    for d in ("docs", "state", "refs"):
        Path(d).mkdir(exist_ok=True)
    for f in ESTADO:
        alvo = Path(f)
        modelo = MODELOS / alvo.name
        if alvo.exists():
            print("  existe  " + f)
        elif modelo.exists():
            shutil.copyfile(modelo, alvo)
            print("  criado  " + f)
        else:
            print("  vazio   " + f + " (modelo ausente)")
    print("")
    print("Agora: preencher CLAUDE.md com o contexto do projeto.")
    print("Depois: " + ENTRADA + " check")
    return 0


def novo(args):
    caminho = ""
    if "--caminho" in args:
        i = args.index("--caminho")
        caminho = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    return rodar("novo", args[0] if args else "", caminho)


def index(_args):
    rc = rodar("gen_index", "--write")
    if rc == 0:
        print("  docs/_index.md regenerado")
    return rc


def bash():
    """O bash do Git, no Windows; o do sistema, no resto.

    Chamar "bash" pelo nome nao serve no Windows: o CreateProcess procura em
    System32 ANTES do PATH, e acha o bash do WSL — que nao enxerga `D:/` e rodaria
    o Python errado. O make escondia isso porque rodava dentro do Git Bash."""
    if sys.platform != "win32":
        return shutil.which("bash") or "bash"
    git = shutil.which("git")
    if git:
        for raiz in Path(git).resolve().parents:
            for rel in ("bin/bash.exe", "usr/bin/bash.exe"):
                if (raiz / rel).exists():
                    return str(raiz / rel)
    achado = shutil.which("bash")
    if achado and "system32" not in achado.lower() and "windowsapps" not in achado.lower():
        return achado
    return None


def test(_args):
    exe = bash()
    if not exe:
        print("  bash não encontrado. A bateria precisa do Git Bash no Windows.")
        return 1
    # as_posix: o bash trata a barra invertida como escape, e o caminho chegaria
    # colado ("D:projetos...").
    return subprocess.run([exe, (AQUI / "harness.sh").as_posix(), ".", ".harness-out"]).returncode


def mcp_list(_args):
    mcp = Path(".mcp.json")
    if mcp.exists():
        print("== MCP do projeto (.mcp.json) ==")
        for nome in json.loads(mcp.read_text(encoding="utf-8")).get("mcpServers", {}):
            print("  " + nome)
    else:
        print("  sem .mcp.json neste projeto (veja .mcp.json.example)")
    try:
        subprocess.run(["claude", "mcp", "list"])
    except OSError:
        print("  'claude' fora do PATH: só a lista do .mcp.json acima.")
    return 0


def _um_argumento(modulo):
    return lambda args: rodar(modulo, args[0] if args else "", *args[1:])


COMANDOS = {
    "novo": novo,
    "adotar": lambda args: rodar("adotar", *args),
    "atualizar": lambda args: rodar("atualizar", *args),
    "release": _um_argumento("release"),
    "init": init,
    "bootstrap": _um_argumento("bootstrap"),
    "check": lambda args: rodar("check"),
    "test": test,
    "index": index,
    "intake": lambda args: rodar("intake"),
    "adr": lambda args: rodar("new_adr", *args),
    "dt": lambda args: rodar("new_dt", *args),
    "doc": _um_argumento("new_doc"),
    "mcp-list": mcp_list,
}


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("help", "-h", "--help", "ajuda"):
        return ajuda()
    cmd, resto = args[0], args[1:]
    if cmd not in COMANDOS:
        print("  comando desconhecido: " + cmd)
        print("  " + ENTRADA + " sem argumento lista os comandos.")
        return 1
    return COMANDOS[cmd](resto)


if __name__ == "__main__":
    sys.exit(main())
