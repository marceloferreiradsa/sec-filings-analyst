#!/bin/bash
# Bateria de regressao dos geradores do template.
#
# Por que existe: os geradores so se exercitam contra documentos reais, e um
# template esta vazio por definicao. Este script FABRICA os documentos que
# faltam — ADRs, dividas, gaps, refs/ com markdown, PDF, planilha, CSV e
# manifesto — e roda todos os comandos contra eles, incluindo os caminhos de
# erro (indice defasado, doc repetido, bootstrap sem NAME, bootstrap duas vezes).
#
# Uso tipico, antes e depois de uma mudanca:
#     bash metodo/harness.sh . /tmp/antes      # com o codigo atual
#     ...faca a mudanca...
#     bash metodo/harness.sh . /tmp/depois
#     diff /tmp/antes/saida.txt /tmp/depois/saida.txt
#
# Diferenca vazia = a mudanca nao alterou comportamento. Qualquer diferenca
# precisa ser uma que voce esperava.
#
# Nada e executado dentro do projeto: tudo roda numa copia descartavel.
set -u
ORIG="$(cd "${1:-.}" && pwd)"
OUT="${2:-./.harness-out}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"

# O fixture mora fora do projeto: rodar `python -m metodo test` na raiz copiaria a pasta
# para dentro dela mesma, e a copia arrastaria a saida da rodada anterior.
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
FX="$STAGE/fixture"
cp -r "$ORIG" "$FX"
rm -rf "$FX/.git" "$FX/.harness-out"
cd "$FX" || exit 1

mkdir -p docs refs

cat > docs/decisoes_arquiteturais.md <<'EOF'
# Decisoes Arquiteturais

---

<a id="adr-01"></a>

## ADR-01 — Banco relacional em vez de documento

**Status:** Ativa

texto

---

## ADR-02 — Chave estrangeira adotada por hipotese

**Status:** Registrada mas pendente

texto

---
EOF

cat > docs/dividas_tecnicas.md <<'EOF'
# Dividas Tecnicas

## DT-01 — Chave sem confirmacao da origem

**Status:** Aberta
**Prioridade:** Alta

## DT-02 — Coluna preenchida porem zerada

**Status:** Aceita
**Prioridade:** Baixa

Conviver: o custo de corrigir supera o beneficio nesta fase.
EOF

cat > docs/gaps.md <<'EOF'
# Gaps de informacao

### I.11 — Campo ausente no export

texto

### I.12 — Orfao na dimensao cliente

texto
EOF

cat > refs/manual_cliente.md <<'EOF'
# Manual do cliente

## 3. Regras de faturamento

### 3.1 Arredondamento

texto

## 4. Glossario
EOF

cat > docs/achados.md <<'EOF'
# Achados

## ACH-001 · Separador errado, nao entra no indice

texto

## ACH-002 · Outro que passa perto

texto

## ACH-003 — Este casa e entra

texto
EOF

# AB-21: o formato mais natural de quem numera a mao em portugues. Escapava do
# indice e do aviso de "quase casa" ao mesmo tempo.
cat > docs/decisoes_projeto.md <<'EOF'
# Decisoes do projeto

## Decisão 1 — Usar FAISS

texto

## 1. Contexto

texto
EOF

# Documento de procedimento: vivo, sem registro nenhum, e com 3 secoes.
cat > docs/pipeline.md <<'EOF'
# Pipeline de dados

## Extrair

## Transformar

## Carregar
EOF

printf 'PDF-falso' > refs/especificacao.pdf
printf 'XLSX-falso' > refs/verificacoes.xlsx
printf 'CSV,falso\n1,2\n' > refs/amostra.csv
printf 'binario' > refs/desconhecido.bin

cat > refs/_fontes.md <<'EOF'
# Fontes externas

| Arquivo | O que e | Derivado em |
|---|---|---|
| `especificacao.pdf` | Especificacao do cliente v2 | `manual_cliente.md` |
| `manual_cliente.md` | Versao indexada do PDF | — |
| `verificacoes.xlsx` | Planilha de verificacoes | n/a — nao vale derivar |
| `amostra.csv` | Amostra de dados | — |
| `desconhecido.bin` | Arquivo opaco | — |
| `sumiu.docx` | Declarado mas ausente | — |
EOF

run () { echo "===== $1 ====="; shift; "$@" 2>&1; echo "[exit=$?]"; }
# Repositorio git com tudo commitado: o `atualizar` exige arvore limpa.
repo () {
  git -C "$1" init -q -b main
  git -C "$1" config core.autocrlf false
  git -C "$1" add -A
  git -C "$1" -c user.name=t -c user.email=t@t commit -q -m "${2:-inicial}"
}
commit () { git -C "$1" add -A; git -C "$1" -c user.name=t -c user.email=t@t commit -q -m "$2"; }

# Procedimento com passos numerados: forma de registro, e nao e registro. O
# marcador tira o documento dos avisos sem mexer nos titulos.
cat > docs/deploy.md <<'EOF'
<!-- metodo: sem-registros -->
# Deploy

## Step 1 — Build

## Step 2 — Ship

## Step 3 — Run
EOF

{
  run "gen_index stdout"             python metodo/gen_index.py
  run "gen_index --check (defasado)" python metodo/gen_index.py --check
  run "gen_index --write"            python metodo/gen_index.py --write
  run "gen_index --check (em dia)"   python metodo/gen_index.py --check
  run "check (fixture nao tem git)"  python metodo/check.py
  echo "===== docs/_index.md ====="; cat docs/_index.md
  run "intake"                       python metodo/intake.py
  run "new_doc"                      python metodo/new_doc.py contrato_de_dados
  echo "===== docs/contrato_de_dados.md ====="; cat docs/contrato_de_dados.md
  run "new_doc (repetido)"           python metodo/new_doc.py contrato_de_dados
  echo "===== new_adr (stdin) ====="; printf 'Formato de particionamento\n' | python metodo/new_adr.py 2>&1; echo "[exit=$?]"
  echo "===== new_dt (stdin) ====="
  printf 'Bridge sem relacionamento ativo\n' | python metodo/new_dt.py 2>&1; echo "[exit=$?]"
  # Titulo por argumento, com acento: e como o agente chama, sem terminal.
  echo "===== adr e dt por argumento ====="
  python -m metodo adr "Decisão por argumento" 2>&1; echo "[exit=$?]"
  python -m metodo dt "Dívida por argumento" 2>&1; echo "[exit=$?]"
  grep "^## ADR-" docs/decisoes_arquiteturais.md | tail -1
  grep "^## DT-" docs/dividas_tecnicas.md | tail -1
  # Sem titulo e sem terminal: sai sem gravar, e sem criar o documento.
  echo "===== adr e dt sem titulo (nada gravado) ====="
  antes=$(cat docs/decisoes_arquiteturais.md docs/dividas_tecnicas.md | cksum)
  python -m metodo adr < /dev/null 2>&1; echo "[exit=$?]"
  python -m metodo dt < /dev/null 2>&1; echo "[exit=$?]"
  [ "$antes" = "$(cat docs/decisoes_arquiteturais.md docs/dividas_tecnicas.md | cksum)" ] && echo "documentos intactos"
  SEM="$STAGE/sem-docs"; mkdir -p "$SEM"; M="$PWD/metodo"
  (cd "$SEM" && python "$M/new_adr.py" < /dev/null > /dev/null 2>&1; python "$M/new_dt.py" < /dev/null > /dev/null 2>&1)
  ls "$SEM/docs" 2>/dev/null || echo "nenhum documento criado"
  echo "===== dividas_tecnicas.md apos DT ====="; cat docs/dividas_tecnicas.md
  echo "===== decisoes_arquiteturais.md apos ADR ====="; cat docs/decisoes_arquiteturais.md
  run "gen_index apos ADR"           python metodo/gen_index.py --write
  echo "===== _index.md final ====="; cat docs/_index.md
  echo "===== release (sem argumento) ====="
  python metodo/release.py "" 2>&1; echo "[exit=$?]"
  echo "===== release (arvore limpa do template) ====="
  python metodo/release.py "$STAGE/release" 2>&1; echo "[exit=$?]"
  echo "===== arvore do release: sem state/ e sem docs/ ====="
  find "$STAGE/release" -type f | sort | sed "s|.*/release/||"
  echo "===== novo (sem argumento) ====="
  python metodo/novo.py "" "" 2>&1; echo "[exit=$?]"
  echo "===== novo (caminho feliz, template ainda virgem) ====="
  python metodo/novo.py "" "$STAGE/derivado" 2>&1; echo "[exit=$?]"
  echo "===== check do projeto derivado ====="
  (cd "$STAGE/derivado" && python metodo/check.py 2>&1); echo "[exit=$?]"
  echo "===== changelog do derivado: entrada de adocao datada ====="
  grep -n "Adoção do método\|Versão do template" "$STAGE/derivado/state/changelog.md" \
    | sed "s/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/DATA/"
  echo "===== adotar (sem argumento) ====="
  python metodo/adotar.py "" 2>&1; echo "[exit=$?]"
  # Caso B real: Makefile proprio com alvos de nome curto, pasta tools/ propria,
  # CLAUDE.md antigo, .gitignore parcial, arvore suja e artefato grande na raiz.
  EX="$STAGE/existente"
  mkdir -p "$EX/src" "$EX/tools"
  printf 'index:\n\t@echo projeto-constroi-faiss\nclean:\n\t@echo projeto-apaga-embeddings\n' > "$EX/Makefile"
  cp "$EX/Makefile" "$STAGE/Makefile.original"
  printf 'print("check do projeto")\n' > "$EX/tools/check.py"
  printf '# Notas antigas do projeto\n\nUsa FAISS.\n' > "$EX/CLAUDE.md"
  printf 'node_modules/\n.env\n' > "$EX/.gitignore"
  printf 'print(1)\n' > "$EX/src/app.py"
  git -C "$EX" init -q -b main
  git -C "$EX" config core.autocrlf false
  git -C "$EX" add -A
  git -C "$EX" -c user.name=t -c user.email=t@t commit -q -m inicial
  printf 'print(2)\n' > "$EX/src/app.py"
  head -c 11000000 /dev/zero > "$EX/imagem.tar.gz"
  echo "===== adotar (projeto existente) ====="
  python metodo/adotar.py "$EX" "Projeto Existente" 2>&1; echo "[exit=$?]"
  echo "===== Makefile do existente: byte a byte igual ao original? ====="
  cmp "$STAGE/Makefile.original" "$EX/Makefile" && echo "identico"
  echo "===== tools/ do projeto intacto ====="; cat "$EX/tools/check.py"
  echo "===== make index no existente continua sendo o do projeto ====="
  make -s -C "$EX" index 2>&1; echo "[exit=$?]"
  echo "===== python -m metodo index no existente ====="
  (cd "$EX" && python -m metodo index 2>&1); echo "[exit=$?]"
  echo "===== CLAUDE.anterior.md preservado ====="; cat "$EX/CLAUDE.anterior.md"
  echo "===== .gitignore do existente ====="; cat "$EX/.gitignore"
  echo "===== adotar de novo (deve recusar) ====="
  python metodo/adotar.py "$EX" "" 2>&1; echo "[exit=$?]"
  # Colisao em arquivo comum do metodo: recusa e nao escreve nada.
  CO="$STAGE/colide"
  mkdir -p "$CO/refs"
  printf 'meu readme\n' > "$CO/refs/README.md"
  echo "===== adotar com refs/README.md do projeto (deve recusar) ====="
  python metodo/adotar.py "$CO" "" 2>&1; echo "[exit=$?]"
  echo "===== nada foi escrito no colide ====="; find "$CO" -type f | sed "s|$STAGE/||" | sort
  # Pasta do projeto com o nome do pacote: recusa, porque o metodo precisa dele.
  PM="$STAGE/pasta-metodo"
  mkdir -p "$PM/metodo"
  printf 'x\n' > "$PM/metodo/notas.txt"
  echo "===== adotar com pasta metodo/ do projeto (deve recusar) ====="
  python metodo/adotar.py "$PM" "" 2>&1; echo "[exit=$?]"
  echo "===== python -m metodo: ajuda, comando desconhecido, codigo de saida ====="
  python -m metodo 2>&1 | head -3; echo "[exit=$?]"
  python -m metodo nao-existe 2>&1; echo "[exit=$?]"
  # O derivado nao tem git: so o indice pode reprovar, e e ele que se testa aqui.
  (cd "$STAGE/derivado" && python -m metodo check > /dev/null 2>&1); echo "[check em dia: exit=$?]"
  printf '# Decisoes\n\n## ADR-09 — registro novo sem reindexar\n' > "$STAGE/derivado/docs/decisoes.md"
  (cd "$STAGE/derivado" && python -m metodo check > /dev/null 2>&1); echo "[check defasado: exit=$?]"
  # ---------------- atualizar: as tres formas antigas ----------------
  # Estado minimo comum: so o que o atualizar le.
  base () {
    mkdir -p "$1/state" "$1/docs" "$1/tools" "$1/.template"
    printf '# Aberto\n\n---\n\n## Geral\n' > "$1/state/aberto.md"
    printf '# Changelog\n' > "$1/state/changelog.md"
    printf '# Decisoes\n\n## ADR-01 — Algo\n\nVer make %s.\n' "$2" > "$1/docs/decisoes.md"
    for s in help gen_index check check_state; do printf '# velho\n' > "$1/tools/$s.py"; done
    printf 'velho\n' > "$1/.template/handoff.md"
    printf 'velho\n' > "$1/METODO.md"
  }
  # Forma 1: cp antigo, Makefile inteiro do template.
  FA="$STAGE/forma-cp"; base "$FA" index
  printf '.PHONY: help index check clean\nhelp:\n\t@python tools/help.py\nindex:\n\t@python tools/gen_index.py --write\ncheck:\n\t@python tools/check.py\nclean:\n\t@find . -name x\n\t@echo "  cache removido (docs/ e state/ intactos)"\n' > "$FA/Makefile"
  printf '# Projeto A\n\nRodar `make check`, depois `make index`. Limpar com `make clean`.\n' > "$FA/CLAUDE.md"
  # Handoff citando alvo do metodo: o atualizar aponta, nao reescreve.
  printf '# Handoff\n\nDepois de mudar registro, `make index`.\n' > "$FA/state/handoff.md"
  repo "$FA"
  # Forma 2: contorno local; o projeto tem index e check proprios.
  FB="$STAGE/forma-contorno"; base "$FB" docs-index
  printf 'index:\n\t@python pipeline.py --only index\ncheck:\n\t@docker compose up\n\n# ---\n# metodo — alvos do ai-project-framework (ADR-14). Manter no FIM.\n# ---\ninclude metodo.mk\n' > "$FB/Makefile"
  printf 'docs-index:\n\t@python tools/gen_index.py --write\ndocs-check:\n\t@python tools/check.py\nmetodo-clean:\n\t@echo "  cache removido (docs/ e state/ intactos)"\n' > "$FB/metodo.mk"
  # O segundo paragrafo descreve a estrutura antiga: a citacao troca, o texto em
  # volta fica falso, e isso vira pendencia.
  printf '# Projeto B\n\n`make index` constroi o FAISS; `make check` sobe o Docker.\n\nO do metodo mora em `metodo.mk`: `make docs-check` e `make docs-index`.\n' > "$FB/CLAUDE.md"
  # Sem VERSAO: a origem so esta na entrada de adocao do changelog.
  printf '\n## 2026-10-20 — Adoção do método\n\nEstrutura do `ai-project-framework` (versão `2f39f84`) instalada.\n' >> "$FB/state/changelog.md"
  repo "$FB"
  # Forma 3: a versao metodo-* (6c58678), com stub de Makefile e VERSAO na raiz.
  FC="$STAGE/forma-prefixo"; base "$FC" metodo-index
  printf '# Makefile do projeto\n#\n# Os alvos do metodo moram em metodo.mk.\n\ninclude metodo.mk\n' > "$FC/Makefile"
  printf 'metodo-check:\n\t@python tools/check.py\nmetodo-index:\n\t@python tools/gen_index.py --write\n' > "$FC/metodo.mk"
  printf 'template gerado em 2026-10-24\norigem: commit 6c58678 do repositorio\n' > "$FC/VERSAO"
  printf '# Projeto C\n\nRodar `make metodo-check`.\n' > "$FC/CLAUDE.md"
  repo "$FC"
  echo "===== atualizar --simular (forma cp): nada gravado ====="
  python metodo/atualizar.py "$FA" --simular 2>&1 | grep -v "^  removido   tools/"; echo "[exit=$?]"
  git -C "$FA" status --short | sed 's/^/  sujo: /'; echo "[status vazio acima = nada gravado]"
  for F in "$FA" "$FB" "$FC"; do
    echo "===== atualizar ($(basename $F)) ====="
    python metodo/atualizar.py "$F" 2>&1 | grep -v "^  removido   tools/"; echo "[exit=$?]"
    echo "--- Makefile:"; [ -f "$F/Makefile" ] && cat "$F/Makefile" || echo "(apagado)"
    echo "--- CLAUDE.md:"; sed -n '3,$p' "$F/CLAUDE.md"
    echo "--- sobras antigas:"; ls -d "$F/tools" "$F/.template" "$F/metodo.mk" "$F/METODO.md" "$F/VERSAO" 2>/dev/null | sed "s|$STAGE/||"
    echo "--- pendencias AT:"; grep "^\*\*AT-" "$F/state/aberto.md"
    echo "--- onde ha citacao antiga:"; grep -A1 "Citações a alvos antigos" "$F/state/aberto.md" | tail -1 | sed 's/\. Não foram.*//'
    echo "--- metodo roda:"; (cd "$F" && python -m metodo index 2>&1); echo "[exit=$?]"
  done
  echo "===== atualizar com arvore suja (deve recusar) ====="
  python metodo/atualizar.py "$FA" 2>&1; echo "[exit=$?]"
  echo "===== atualizar de novo, ja na forma nova (contorno) ====="
  commit "$FB" atualizado
  python metodo/atualizar.py "$FB" 2>&1; echo "[exit=$?]"
  echo "--- mudou algo alem do esperado?"; git -C "$FB" status --short
  echo "===== atualizar em projeto sem o metodo (deve recusar) ====="
  python metodo/atualizar.py "$CO" 2>&1; echo "[exit=$?]"
  run "bootstrap sem NAME"           python metodo/bootstrap.py ""
  run "bootstrap"                    python metodo/bootstrap.py "Projeto de Teste"
  echo "===== CLAUDE.md cabecalho ====="; head -12 CLAUDE.md
  echo "===== README.md pos-bootstrap ====="; cat README.md
  run "bootstrap (2a vez)"           python metodo/bootstrap.py "Projeto de Teste"
  # O fixture ja traz decisoes_arquiteturais.md, entao o caminho de CRIAR o
  # documento do zero nao era exercitado. Apaga e roda de novo.
  rm -f docs/decisoes_arquiteturais.md
  rm -f docs/dividas_tecnicas.md
  echo "===== new_dt criando o documento do zero ====="
  printf 'Cabecalho novo de dividas\n' | python metodo/new_dt.py 2>&1; echo "[exit=$?]"
  echo "===== cabecalho de dividas gerado ====="; head -22 docs/dividas_tecnicas.md
  echo "===== new_adr criando o documento do zero ====="
  printf 'Cabecalho novo\n' | python metodo/new_adr.py 2>&1; echo "[exit=$?]"
  echo "===== cabecalho gerado ====="; head -14 docs/decisoes_arquiteturais.md
  # O fixture copia o handoff real do template, entao o caminho de "adocao
  # incompleta" nao era exercitado. Repoe o modelo e roda de novo.
  cp metodo/modelos/handoff.md state/handoff.md
  run "check (handoff ainda e o modelo)"  python metodo/check.py
  echo "===== novo a partir de projeto ja adotado (deve recusar) ====="
  python metodo/novo.py "" "$STAGE/outro" 2>&1; echo "[exit=$?]"
  echo "===== arvore final ====="; find . -type f | sort
} > "$OUT/saida.txt" 2>&1

echo "gravado: $OUT/saida.txt ($(wc -l < "$OUT/saida.txt") linhas)"
grep -c "Traceback" "$OUT/saida.txt" | sed 's/^/tracebacks: /'
echo "AVISO: zero tracebacks nao e aprovacao. Esta bateria e um COMPARADOR —"
echo "       guarde a saida antes da mudanca e rode diff contra esta. Defeito de"
echo "       conteudo (nome errado, texto faltando) nao levanta excecao nenhuma."
