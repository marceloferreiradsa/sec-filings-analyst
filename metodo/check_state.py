#!/usr/bin/env python3
"""Confere se os arquivos de estado acompanham o trabalho que o git registra.

Sao duas verificacoes, e nenhuma das duas existia porque as duas dependiam de
disciplina — o que o metodo existe para dispensar.

(1) O CHANGELOG. Nao tem automacao: alguem escreve nele por habito. Enquanto o
    changelog e o UNICO lugar do registro, pular a entrada e dificil, porque nao
    ha outro destino para a informacao. Adotar git cria um concorrente: a
    mensagem de commit descreve a mesma mudanca, descarrega o impulso de
    registrar, e a entrada deixa de ser escrita sem que nada acuse. Aconteceu em
    01/09/2026, com duas alteracoes que so entraram horas depois.

(2) O HANDOFF. E derivado do changelog e regenerado no fim da sessao. Quando a
    regeneracao nao acontece, o arquivo MAIS LIDO do metodo passa a mentir com
    aparencia de autoridade — o de 01/09/2026 dizia que o RLS nao existia depois
    de o RLS ter sido implementado. E o mesmo defeito que o metodo ja descreve
    para o indice: responde, e responde errado.

    ATENCAO AO SINAL: comparar DATAS nao serve. Handoff e changelog costumam
    ter a mesma data — o trabalho do dia continua depois de o handoff ser
    escrito, que foi exatamente o caso que originou esta verificacao. O sinal
    correto e a ordem dos commits: se algum commit de conteudo ou de changelog
    veio DEPOIS do ultimo commit que tocou o handoff, o handoff esta atras.

LIMITE CONHECIDO: as duas so funcionam onde ha git. Em projeto sem git nao ha
com o que cruzar, e ali ausencia de registro e indistinguivel de ausencia de
mudanca.
"""
import re
import subprocess
from pathlib import Path

CHANGELOG = Path("state/changelog.md")
HANDOFF = Path("state/handoff.md")

# Escrever estes arquivos E o ato de registrar, nao trabalho a registrar.
IGNORED = ("state/", "docs/_index.md")

# `git log --name-only` separa o cabecalho dos arquivos com uma linha em branco,
# mas NAO separa um commit do seguinte: o proximo cabecalho vem colado no ultimo
# arquivo do anterior. Por isso o cabecalho e reconhecido pela forma — sha, data
# ISO e assunto separados por TAB — em vez de o log ser fatiado por bloco.
HEADER = re.compile(r"^([0-9a-f]{7,40})\t(\d{4}-\d{2}-\d{2})\t(.*)$")


def _git(*args):
    """Devolve stdout limpo, ou None se o git nao responder."""
    try:
        # encoding explicito: sem ele o Python decodifica pela codepage do
        # Windows e assunto de commit com acento sai corrompido na saida.
        r = subprocess.run(("git",) + args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _content(paths):
    return [c for c in paths if c and not c.startswith(IGNORED)]


def _walk(log):
    """Devolve [(sha, data, assunto, [arquivos])] a partir de um log --name-only."""
    commits, current, files = [], None, []
    for line in (log or "").splitlines():
        m = HEADER.match(line)
        if m:
            if current:
                commits.append(current + (files,))
            current, files = m.groups(), []
        elif line.strip():
            files.append(line.strip())
    if current:
        commits.append(current + (files,))
    return commits


def _check_changelog():
    # Data extraida do inicio do cabecalho, sem exigir que ela esteja sozinha
    # na linha: o modelo do template escreve "## AAAA-MM-DD — titulo curto".
    # Parser estrito falha em silencio no primeiro uso — foi o que aconteceu.
    dates = re.findall(r"^##\s+(\d{4}-\d{2}-\d{2})",
                       CHANGELOG.read_text(encoding="utf-8"), re.M)
    if not dates:
        print("  AVISO  nenhum cabeçalho '## AAAA-MM-DD' em state/changelog.md")
        return 1
    latest = max(dates)

    log = _git("log", "--format=%h%x09%ad%x09%s", "--date=short", "--name-only", "-40")
    behind = [(s, d, a) for s, d, a, files_of in _walk(log)
                 if d > latest and _content(files_of)]

    dirty = _content(l[3:] for l in (_git("status", "--porcelain") or "").splitlines())
    last = _git("log", "-1", "--format=%cd", "--date=short") or ""
    pending = bool(dirty) and latest < last

    if not behind and not pending:
        print("  ok     changelog: última entrada " + latest + " cobre o que o git registra")
        return 0
    for sha, date, subject in behind:
        print("  FALTA  changelog: " + sha + " (" + date + ") sem contrapartida: " + subject[:44])
    if pending:
        print("  AVISO  changelog: " + str(len(dirty)) + " arquivo(s) de conteúdo não commitado(s)")
    print("         última entrada é de " + latest + "; anexe o que tem efeito no produto.")
    return 1


def _check_handoff():
    if not HANDOFF.exists():
        print("  --     handoff ausente")
        return 0
    # Handoff alterado e ainda nao commitado significa que alguem acabou de
    # regenera-lo. Sem esta checagem a ferramenta manda fazer o que a pessoa
    # acabou de fazer — instrucao errada e no pior momento, o fim da sessao.
    alvo = str(HANDOFF).replace(chr(92), "/")
    if any(l[3:].strip() == alvo for l in (_git("status", "--porcelain") or "").splitlines()):
        print("  ok     handoff: regenerado, aguardando commit")
        return 0

    base = _git("log", "-1", "--format=%H", "--", alvo)
    if not base:
        print("  AVISO  handoff: nunca commitado — regenere e faça o commit junto do changelog")
        return 1

    log = _git("log", "--format=%h%x09%ad%x09%s", "--date=short", "--name-only", base + "..HEAD")
    after = [(s, a) for s, d, a, files_of in _walk(log)
              if _content(files_of) or "state/changelog.md" in files_of]

    if not after:
        print("  ok     handoff: nada foi commitado depois da última regeneração")
        return 0
    print("  FALTA  handoff: " + str(len(after)) + " commit(s) depois da última regeneração")
    for sha, subject in after[:4]:
        print("         " + sha + "  " + subject[:58])
    print("         Regenere state/handoff.md antes de fechar a sessão ou dar /clear.")
    return 1


def check_state():
    print("== Estado acompanha o git? ==")
    if not CHANGELOG.exists():
        print("  --     state/changelog.md ausente — rode 'python -m metodo init'")
        return 0
    if _git("rev-parse", "--git-dir") is None:
        print("  --     sem git neste projeto: nada com que cruzar")
        print("         O estado é a única fonte; registro pulado não deixa rastro.")
        return 0
    return _check_changelog() or _check_handoff()
