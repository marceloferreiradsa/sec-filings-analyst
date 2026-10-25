#!/usr/bin/env python3
"""Cria um projeto novo a partir do clone do template.

Roda DE DENTRO do clone do template. Copia o metodo para uma pasta nova e chama o
bootstrap la dentro.

Por que existe: o passo 1 da adocao era um `cp -r` manual com uma armadilha
documentada — o ponto depois da barra, que decide se os arquivos ocultos vao
junto. Quem esquece perde `.vscode/` e `.gitattributes`, e so descobre depois.
Um comando remove a armadilha.

E resolve um furo maior: quem adota nao tem uma pasta de projeto padronizada, e
por isso nao tem o COMO-ADOTAR.md em maos no momento em que precisa dele. Aqui o
ponto de partida e o proprio template, entao o guia viaja junto e e apagado no
fim da adocao — igual ao PRIMEIRA-SESSAO.md.

Uso:
    python -m metodo novo "Meu Projeto"                          # cria ../meu-projeto
    python -m metodo novo --caminho C:/projetos/meu-projeto      # caminho completo
    python -m metodo novo "Meu Projeto" --caminho ...            # os dois
"""
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# --- Valores especificos do idioma. Para uma versao em outro idioma, e so
# --- traduzir este bloco: o resto do script nao tem texto embutido.
GUIA = "COMO-ADOTAR.md"
PLACEHOLDER = "{NOME DO PROJETO}"

# O que o metodo leva para o projeto novo. Lista explicita, e nao "tudo menos":
# assim nada do template vaza para o projeto por esquecimento — nem os docs/ e
# state/ deste repositorio, nem integracoes locais.
#
# Tudo o que e do metodo mora numa pasta so — scripts, modelos, racional e
# VERSAO. `metodo/` e `metodo/modelos/` na raiz colidiam com pastas do projeto, como
# o Makefile colidia com o dele. Na raiz fica so o que o Claude Code e o VS Code
# procuram ali (CLAUDE.md, mcp/, .vscode/) e o que e do projeto.
PACOTE = "metodo"
MODELOS = PACOTE + "/modelos"
# O VERSAO so existe no pacote publicado (o release o grava). Viaja dentro da
# pasta: sem ele, o projeto nao sabia de que versao veio.
VERSAO = PACOTE + "/VERSAO"
ARQUIVOS = ["CLAUDE.md", GUIA, ".gitattributes", ".gitignore", ".mcp.json.example"]
PASTAS = [PACOTE, "refs", "mcp", ".vscode"]


def apelido(nome):
    """'Meu Projeto' -> 'meu-projeto'. Sem acento: nome de pasta e identificador."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", nome)
                         if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


# Conectores nao entram maiusculos: "Analise De Margem" denuncia geracao
# automatica logo na primeira linha do CLAUDE.md.
CONECTORES = {"de", "da", "do", "das", "dos", "e", "em", "no", "na", "para", "a", "o"}


def humanizar(pasta):
    """'analise-de-margem' -> 'Analise de Margem', quando so o caminho foi dado."""
    partes = [p for p in re.split(r"[-_]+", pasta) if p]
    return " ".join(p.capitalize() if i == 0 or p.lower() not in CONECTORES else p.lower()
                    for i, p in enumerate(partes))


def main():
    nome = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    caminho = (sys.argv[2] if len(sys.argv) > 2 else "").strip()

    if not nome and not caminho:
        print('  uso: python -m metodo novo "Meu Projeto"')
        print('       python -m metodo novo --caminho "C:/projetos/meu-projeto"')
        print("")
        print("  NOME sozinho cria a pasta ao lado do template.")
        print("  CAMINHO sozinho deriva o nome do projeto da última pasta.")
        return 1

    if not Path("CLAUDE.md").exists() or not Path(MODELOS).is_dir():
        print("  Este comando roda de dentro do clone do template.")
        print("  Não encontrei CLAUDE.md e " + MODELOS + "/ aqui.")
        return 1

    # Sem esta guarda, rodar a partir de um projeto ja adotado copiaria o
    # CLAUDE.md dele — e o bootstrap recusaria depois da copia, deixando a pasta
    # criada pela metade. Falhar antes de criar qualquer coisa e mais barato.
    if PLACEHOLDER not in Path("CLAUDE.md").read_text(encoding="utf-8"):
        print("  O CLAUDE.md daqui já foi personalizado: esta pasta é um projeto")
        print("  adotado, não o template. Rode de dentro do clone do template.")
        return 1

    destino = Path(caminho) if caminho else Path("..") / apelido(nome)
    if not nome:
        nome = humanizar(destino.resolve().name)

    if destino.exists() and any(destino.iterdir()):
        print("  A pasta já existe e não está vazia: " + str(destino))
        print("  Abortando para não sobrescrever. Escolha outro CAMINHO.")
        return 1

    destino.mkdir(parents=True, exist_ok=True)
    for f in ARQUIVOS:
        if Path(f).exists():
            shutil.copyfile(f, destino / f)
    for d in PASTAS:
        if Path(d).is_dir():
            shutil.copytree(d, destino / d, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    print("  copiado    o método para " + str(destino))
    # flush obrigatório: sem ele o buffer do pai solta depois do que o filho já
    # escreveu direto no terminal, e a saída sai fora de ordem.
    sys.stdout.flush()
    r = subprocess.run([sys.executable, "-m", PACOTE, "bootstrap", nome],
                       cwd=str(destino), encoding="utf-8")
    if r.returncode != 0:
        print("  O bootstrap falhou. A pasta ficou criada em " + str(destino) + ".")
        return 1

    print("")
    print("  Agora, na pasta nova:")
    print("    cd " + str(destino))
    print("    git init -b main")
    print("    claude")
    print("")
    print("  E peça ao agente: \"leia o " + GUIA + " e me guie na adoção\".")
    print("  O guia viajou junto de propósito, e o último passo dele é apagá-lo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
