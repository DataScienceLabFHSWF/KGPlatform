.PHONY: bootstrap up down logs health build infra \
        standalone-kgb standalone-qa standalone-onto \
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
	@echo "=== Port Map ==="
	@echo "  8001  KGBuilder API     18134  Ollama (KGBuilder)"
	@echo "  8002  GraphQA API       18136  Ollama (GraphQA)"
	@echo "  8010  Ontology API      18135  Ollama (Ontology)"
	@echo "  8501  Streamlit UI"
	@echo "  7474  Neo4j Browser     6333   Qdrant    3030  Fuseki"
	echo "See CONSOLIDATION.md for architecture & wiring strategy"
