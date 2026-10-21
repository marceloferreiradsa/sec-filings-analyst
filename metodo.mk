# Metodo (ai-project-framework) — alvos de estrutura e documentacao
#
# Incluido no FIM do Makefile do projeto (`include metodo.mk`). No fim, e nao
# no topo: o primeiro alvo lido vira o padrao de `make` sem argumento, e o
# padrao deste projeto e o `help` dele, nao o do metodo.
#
# Alvos que colidiam com os do projeto foram renomeados do lado do metodo
# (mesma solucao do constituicao-stf, ADR-14 de la):
#   check -> docs-check    (o check do projeto e build/run/test/stop do Docker)
#   index -> docs-index    (o index do projeto constroi o FAISS)
#   help  -> metodo-help   (o help do projeto e o alvo padrao)
#   test  -> metodo-test   (o test do projeto testa o container)
#   clean -> metodo-clean  (o clean do projeto APAGA data/raw e data/processed)
#
# As mensagens de `@echo` usam so palavras sem acento, de proposito: `@echo`
# sai pela codepage do terminal e corrompe acento no Windows. Texto com acento
# vive em tools/*.py.
#
# Alvos idempotentes: rodar duas vezes nao quebra nada e nao sobrescreve conteudo.

.PHONY: metodo-help init novo release bootstrap docs-check docs-index intake adr dt doc session mcp-list metodo-clean tree metodo-test

metodo-help:
	@python tools/help.py

novo:
	@python tools/novo.py "$(NOME)" "$(CAMINHO)"

release:
	@python tools/release.py "$(DESTINO)"

init:
	@mkdir -p docs state tools mcp refs
	@for f in state/handoff.md state/changelog.md state/aberto.md docs/_index.md; do \
		if [ ! -f "$$f" ]; then cp -n ".template/$$(basename $$f)" "$$f" 2>/dev/null \
			&& echo "  criado  $$f" || echo "  vazio   $$f (modelo ausente)"; \
		else echo "  existe  $$f"; fi; done
	@echo ""
	@echo "Agora: preencher CLAUDE.md com o contexto do projeto."
	@echo "Depois: make docs-check"

bootstrap:
	@python tools/bootstrap.py "$(NAME)"

docs-check:
	@python tools/check.py

intake:
	@python tools/intake.py

metodo-test:
	@bash tools/harness.sh . .harness-out

docs-index:
	@python tools/gen_index.py --write
	@echo "  docs/_index.md regenerado"

adr:
	@python tools/new_adr.py

dt:
	@python tools/new_dt.py

doc:
	@if [ -z "$(DOC)" ]; then echo "  uso: make doc DOC=nome_do_documento"; exit 1; fi
	@python tools/new_doc.py "$(DOC)"

session:
	@claude --continue || echo "  'claude' fora do PATH. Instale a CLI ou use o plugin do VS Code."

mcp-list:
	@if [ -f ".mcp.json" ]; then \
		echo "== MCP do projeto (.mcp.json) =="; python -c "import json;d=json.load(open('.mcp.json'));[print('  '+k) for k in d.get('mcpServers',{})]"; \
	else echo "  sem .mcp.json neste projeto (veja .mcp.json.example)"; fi
	@claude mcp list 2>/dev/null || true

tree:
	@find . -maxdepth 2 -not -path './.git/*' -not -path './.template/*' -not -path './.sec-analysis/*' | sort

metodo-clean:
	@find . -path ./.sec-analysis -prune -o -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -path ./.sec-analysis -prune -o -name '*.pyc' -delete 2>/dev/null || true
	@echo "  cache removido (docs/, state/ e data/ intactos)"
