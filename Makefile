.PHONY: bootstrap up down logs health build infra \
        standalone-kgb standalone-qa standalone-onto \
        paper-check paper-pull paper-kgb paper-onto paper-qa paper-all \
        help

# ============================================================
# Full Platform (all services + frontend + infra)
# ============================================================

up:
	@echo "Starting KGPlatform (infra + model pulls + APIs + frontend)..." && \
	docker compose up -d
	@echo "Done. Models will be pulled in the background if not cached."
	@echo "Run 'make health' to check when everything is ready."

down:
	@echo "Stopping KGPlatform..." && \
	docker compose down

logs:
	docker compose logs -f

build:
	@echo "Building all service images..." && \
	docker compose build

health:
	@bash scripts/health_check.sh

bootstrap:
	@bash scripts/bootstrap.sh

# Infrastructure only (no API services or frontend)
infra:
	docker compose up -d neo4j qdrant fuseki \
		ollama-kgbuilder ollama-graphqa ollama-ontology \
		ollama-kgbuilder-init ollama-graphqa-init ollama-ontology-init

# ============================================================
# Standalone Mode — run each submodule independently
# ============================================================

standalone-kgb:
	@echo "Starting KnowledgeGraphBuilder standalone..." && \
	cd repos/KnowledgeGraphBuilder && docker compose up -d

standalone-qa:
	@echo "Starting GraphQAAgent standalone..." && \
	cd repos/GraphQAAgent && docker compose up -d

standalone-onto:
	@echo "Starting OntologyExtender standalone..." && \
	cd repos/OntologyExtender && docker compose up -d

# ============================================================
# Help
# ============================================================

help:
	@echo "KGPlatform — Orchestration for KG research ecosystem"
	@echo ""
	@echo "=== Full Platform ==="
	@echo "  make up            - Start everything (infra + APIs + frontend)"
	@echo "  make down          - Stop everything"
	@echo "  make build         - Build all service images"
	@echo "  make logs          - Follow logs"
	@echo "  make health        - Check service health"
	@echo "  make bootstrap     - Initialize .env, submodules, pull images"
	@echo "  make infra         - Start infra only (Neo4j, Qdrant, Fuseki, Ollama)"
	@echo ""
	@echo "=== Standalone Repos ==="
	@echo "  make standalone-kgb   - KnowledgeGraphBuilder standalone stack"
	@echo "  make standalone-qa    - GraphQAAgent standalone stack"
	@echo "  make standalone-onto  - OntologyExtender standalone stack"
	@echo ""
	@echo "=== Paper Experiments ==="
	@echo "  make paper-check      - Verify all infra + models ready"
	@echo "  make paper-pull       - Pull all required models into Ollama containers"
	@echo "  make paper-kgb        - KGBuilder paper (6 conditions × 3 runs)"
	@echo "  make paper-onto       - OntologyExtender paper (debate + OntoURL)"
	@echo "  make paper-qa         - GraphQAAgent paper (6 strategies + DeepEval)"
	@echo "  make paper-all        - Run ALL paper experiments (sequential)"
	@echo ""
	@echo "=== Port Map ==="
	@echo "  8001  KGBuilder API     18134  Ollama (KGBuilder)"
	@echo "  8002  GraphQA API       18136  Ollama (GraphQA)"
	@echo "  8010  Ontology API      18135  Ollama (Ontology)"
	@echo "  8501  Streamlit UI      8081   KG Workbench (kg-ui)"
	@echo "  7474  Neo4j Browser     6333   Qdrant    3030  Fuseki"
	@echo ""
	@echo "See CONSOLIDATION.md for architecture & wiring strategy"

# ============================================================
# Paper Experiments — orchestrate from root
# ============================================================
# Run order: KGB first (populates Neo4j/Qdrant), then GraphQA
# (reads from Neo4j/Qdrant), OntologyExtender is independent.
# ============================================================

OLLAMA_KGB  := http://localhost:18134
OLLAMA_QA   := http://localhost:18136
OLLAMA_ONTO := http://localhost:18135

ALL_MODELS := gemma4:e2b gemma4:e4b gemma4:31b nemotron-3-nano qwen3-embedding:latest

paper-check:
	@echo "Checking platform infrastructure..."
	@curl -sf $(OLLAMA_KGB)/api/tags  > /dev/null || { echo "✗ Ollama (KGB) not reachable at $(OLLAMA_KGB)"; exit 1; }
	@curl -sf $(OLLAMA_QA)/api/tags   > /dev/null || { echo "✗ Ollama (QA) not reachable at $(OLLAMA_QA)"; exit 1; }
	@curl -sf $(OLLAMA_ONTO)/api/tags > /dev/null || { echo "✗ Ollama (Onto) not reachable at $(OLLAMA_ONTO)"; exit 1; }
	@curl -sf http://localhost:7474   > /dev/null || { echo "✗ Neo4j not reachable"; exit 1; }
	@curl -sf http://localhost:6333/collections > /dev/null || { echo "✗ Qdrant not reachable"; exit 1; }
	@curl -sf http://localhost:3030/$$/ping     > /dev/null || { echo "✗ Fuseki not reachable"; exit 1; }
	@echo "✓ All infrastructure services reachable"

paper-pull: paper-check
	@echo "Pulling models into all Ollama containers..."
	@for model in gemma4:e2b gemma4:e4b gemma4:31b nemotron-3-nano; do \
		echo "  → ollama-kgbuilder: $$model"; \
		docker exec ollama-kgbuilder ollama pull $$model; \
		echo "  → ollama-ontology: $$model"; \
		docker exec ollama-ontology ollama pull $$model; \
	done
	@echo "  → ollama-graphqa: gemma4:e4b"
	@docker exec ollama-graphqa ollama pull gemma4:e4b
	@echo "  → ollama-graphqa: qwen3-embedding:latest"
	@docker exec ollama-graphqa ollama pull qwen3-embedding:latest
	@echo "✓ All models pulled"

paper-kgb: paper-check
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  KGBuilder Paper — 6 conditions × 3 runs    ║"
	@echo "╚══════════════════════════════════════════════╝"
	cd repos/KnowledgeGraphBuilder && $(MAKE) -f Makefile.paper benchmark

paper-onto: paper-check
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  OntologyExtender Paper — Full experiments   ║"
	@echo "╚══════════════════════════════════════════════╝"
	cd repos/OntologyExtender && $(MAKE) -f Makefile.paper all

paper-qa: paper-check
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  GraphQAAgent Paper — 6 strategies + eval    ║"
	@echo "╚══════════════════════════════════════════════╝"
	cd repos/GraphQAAgent && $(MAKE) -f Makefile.paper all

paper-all: paper-pull paper-kgb paper-qa paper-onto
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  ALL PAPER EXPERIMENTS COMPLETE              ║"
	@echo "╠══════════════════════════════════════════════╣"
	@echo "║  KGB:  repos/KnowledgeGraphBuilder/experiment_results/  ║"
	@echo "║  QA:   repos/GraphQAAgent/reports/comparison/           ║"
	@echo "║  Onto: repos/OntologyExtender/experiment_results/       ║"
	@echo "║        repos/OntologyExtender/results/ontourl/          ║"
	@echo "╚══════════════════════════════════════════════╝"
