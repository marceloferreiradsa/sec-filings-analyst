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
#     bash tools/harness.sh . /tmp/antes      # com o codigo atual
#     ...faca a mudanca...
#     bash tools/harness.sh . /tmp/depois
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

# O fixture mora fora do projeto: rodar `make metodo-test` na raiz copiaria a pasta
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

{
  run "gen_index stdout"             python tools/gen_index.py
  run "gen_index --check (defasado)" python tools/gen_index.py --check
  run "gen_index --write"            python tools/gen_index.py --write
  run "gen_index --check (em dia)"   python tools/gen_index.py --check
  run "check (fixture nao tem git)"  python tools/check.py
  echo "===== docs/_index.md ====="; cat docs/_index.md
  run "intake"                       python tools/intake.py
  run "new_doc"                      python tools/new_doc.py contrato_de_dados
  echo "===== docs/contrato_de_dados.md ====="; cat docs/contrato_de_dados.md
  run "new_doc (repetido)"           python tools/new_doc.py contrato_de_dados
  echo "===== new_adr (stdin) ====="; printf 'Formato de particionamento\n' | python tools/new_adr.py 2>&1; echo "[exit=$?]"
  echo "===== new_dt (stdin) ====="
  printf 'Bridge sem relacionamento ativo\n' | python tools/new_dt.py 2>&1; echo "[exit=$?]"
  echo "===== dividas_tecnicas.md apos DT ====="; cat docs/dividas_tecnicas.md
  echo "===== decisoes_arquiteturais.md apos ADR ====="; cat docs/decisoes_arquiteturais.md
  run "gen_index apos ADR"           python tools/gen_index.py --write
  echo "===== _index.md final ====="; cat docs/_index.md
  echo "===== release (sem argumento) ====="
  python tools/release.py "" 2>&1; echo "[exit=$?]"
  echo "===== release (arvore limpa do template) ====="
  python tools/release.py "$STAGE/release" 2>&1; echo "[exit=$?]"
  echo "===== arvore do release: sem state/ e sem docs/ ====="
  find "$STAGE/release" -type f | sort | sed "s|.*/release/||"
  echo "===== novo (sem argumento) ====="
  python tools/novo.py "" "" 2>&1; echo "[exit=$?]"
  echo "===== novo (caminho feliz, template ainda virgem) ====="
  python tools/novo.py "" "$STAGE/derivado" 2>&1; echo "[exit=$?]"
  echo "===== check do projeto derivado ====="
  (cd "$STAGE/derivado" && python tools/check.py 2>&1); echo "[exit=$?]"
  run "bootstrap sem NAME"           python tools/bootstrap.py ""
  run "bootstrap"                    python tools/bootstrap.py "Projeto de Teste"
  echo "===== CLAUDE.md cabecalho ====="; head -12 CLAUDE.md
  echo "===== README.md pos-bootstrap ====="; cat README.md
  run "bootstrap (2a vez)"           python tools/bootstrap.py "Projeto de Teste"
  # O fixture ja traz decisoes_arquiteturais.md, entao o caminho de CRIAR o
  # documento do zero nao era exercitado. Apaga e roda de novo.
  rm -f docs/decisoes_arquiteturais.md
  rm -f docs/dividas_tecnicas.md
  echo "===== new_dt criando o documento do zero ====="
  printf 'Cabecalho novo de dividas\n' | python tools/new_dt.py 2>&1; echo "[exit=$?]"
  echo "===== cabecalho de dividas gerado ====="; head -22 docs/dividas_tecnicas.md
  echo "===== new_adr criando o documento do zero ====="
  printf 'Cabecalho novo\n' | python tools/new_adr.py 2>&1; echo "[exit=$?]"
  echo "===== cabecalho gerado ====="; head -14 docs/decisoes_arquiteturais.md
  # O fixture copia o handoff real do template, entao o caminho de "adocao
  # incompleta" nao era exercitado. Repoe o modelo e roda de novo.
  cp .template/handoff.md state/handoff.md
  run "check (handoff ainda e o modelo)"  python tools/check.py
  echo "===== novo a partir de projeto ja adotado (deve recusar) ====="
  python tools/novo.py "" "$STAGE/outro" 2>&1; echo "[exit=$?]"
  echo "===== arvore final ====="; find . -type f | sort
} > "$OUT/saida.txt" 2>&1

echo "gravado: $OUT/saida.txt ($(wc -l < "$OUT/saida.txt") linhas)"
grep -c "Traceback" "$OUT/saida.txt" | sed 's/^/tracebacks: /'
echo "AVISO: zero tracebacks nao e aprovacao. Esta bateria e um COMPARADOR —"
echo "       guarde a saida antes da mudanca e rode diff contra esta. Defeito de"
echo "       conteudo (nome errado, texto faltando) nao levanta excecao nenhuma."
