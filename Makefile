# ─── Makefile — SEC Filings Analyst ──────────────────────────────────────────
#
# Wraps the most common commands so you don't have to remember them.
# Run `make` or `make help` to list all available targets.
#
# Prerequisites:
#   - make      (Windows: winget install GnuWin32.Make  or  choco install make)
#   - Docker    (docker.com/get-started)
#   - Python    (with venv active)
#
# External dependency for `make deploy`:
#   - SSH key at $(VPS_KEY) must exist and be authorised on the VPS.
#     Change VPS_HOST and VPS_KEY below to match your environment.
#     The target prints next steps after transfer — VPS commands must be
#     run manually over SSH (no remote shell is opened from here).

# ── Configuration ─────────────────────────────────────────────────────────────

IMAGE     := sec-filings-analyst
CONTAINER := sec-analyst
PORT      := 8501
PACKAGE   := $(IMAGE).tar.gz

# VPS — used only by `make deploy`
VPS_HOST  := root@72.60.148.174
VPS_KEY   := $(HOME)/.ssh/hostinger_key
VPS_DIR   := /root/sec-analyst

# ── Boilerplate ───────────────────────────────────────────────────────────────

.DEFAULT_GOAL := help
.PHONY: help install \
        pipeline ingest chunk embed index status \
        smoke eval ragas \
        build run stop logs shell open test check \
        package deploy \
        clean

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show this help message
	@echo ""
	@echo "  SEC Filings Analyst — available commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────────────

install: ## Install development dependencies (requirements-dev.txt)
	pip install -r requirements-dev.txt

# ── Pipeline ──────────────────────────────────────────────────────────────────

pipeline: ## Run full pipeline — ingest → chunk → embed → index
	python pipeline.py

ingest: ## Run ingestion stage only
	python pipeline.py --only ingest

chunk: ## Run chunking stage only
	python pipeline.py --only chunk

embed: ## Run embedding stage only  (~$0.03)
	python pipeline.py --only embed

index: ## Build FAISS index from existing embeddings
	python pipeline.py --only index

status: ## Show what pipeline stages have been built
	python pipeline.py --status

# ── Evaluation ────────────────────────────────────────────────────────────────

smoke: ## Smoke tests — 5 health checks  (~$0.002, ~30s)
	python -m eval.evaluate --mode smoke

eval: ## Full evaluation — smoke + 20 assertion tests  (~$0.005)
	python -m eval.evaluate --mode all

ragas: ## RAGAS scoring — Faithfulness + Relevancy per claim  (~$0.10)
	python -m eval.evaluate --mode ragas-real

# ── Docker (local) ────────────────────────────────────────────────────────────

build: ## Build Docker image
	docker build -t $(IMAGE) .

run: ## Start container locally (detached, port $(PORT))
	docker run -d -p $(PORT):$(PORT) \
		-e OPENAI_API_KEY=$$OPENAI_API_KEY \
		--name $(CONTAINER) \
		$(IMAGE)
	@echo "→ http://localhost:$(PORT)"

stop: ## Stop and remove local container
	docker rm -f $(CONTAINER)

logs: ## Stream container logs  (Ctrl+C to exit)
	docker logs $(CONTAINER) -f

shell: ## Open an interactive shell inside the container
	docker exec -it $(CONTAINER) /bin/bash

open: ## Open the app in the browser
	@python -c "import webbrowser; webbrowser.open('http://localhost:$(PORT)')"

test: ## Run pre-deployment test suite against running container (20 checks)
	python tests/test_deployment.py

check: ## Full local validation — build → run → test → stop
	$(MAKE) build
	$(MAKE) run
	$(MAKE) test
	$(MAKE) stop

# ── Deployment ────────────────────────────────────────────────────────────────

package: ## Save Docker image to $(PACKAGE) for VPS transfer
	docker save $(IMAGE) | gzip > $(PACKAGE)
	@echo "Saved: $(PACKAGE)"

deploy: package ## Transfer image to VPS (runs package first)
	# Dependency: $(VPS_KEY) must exist and be authorised on $(VPS_HOST).
	# To update the key path: edit VPS_KEY at the top of this file.
	scp -i $(VPS_KEY) $(PACKAGE) $(VPS_HOST):~/
	@echo ""
	@echo "Transfer complete. SSH in and run:"
	@echo "  docker load < ~/$(PACKAGE)"
	@echo "  cd $(VPS_DIR) && docker compose down && docker compose up -d"

# ── Maintenance ───────────────────────────────────────────────────────────────

clean: ## Remove pipeline intermediates — data/raw and data/processed
	# data/index is preserved (FAISS index + chunks.json used by the app).
	# Re-run `make pipeline` to regenerate everything from scratch.
	@echo "Removing data/raw and data/processed..."
	@rm -rf data/raw data/processed
	@echo "Done. data/index preserved."