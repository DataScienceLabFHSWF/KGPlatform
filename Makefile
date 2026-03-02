.PHONY: bootstrap up down logs health build test

bootstrap:
	bash scripts/bootstrap.sh

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

health:
	@echo "KGBuilder:  $$(curl -s http://localhost:8001/api/v1/health | python3 -m json.tool 2>/dev/null || echo 'OFFLINE')"
	@echo "GraphQA:    $$(curl -s http://localhost:8002/api/v1/health | python3 -m json.tool 2>/dev/null || echo 'OFFLINE')"
	@echo "Ontology:   $$(curl -s http://localhost:8003/api/v1/health | python3 -m json.tool 2>/dev/null || echo 'OFFLINE')"

build:
	docker compose build

# Run just infrastructure (no app services)
infra:
	docker compose up -d neo4j qdrant fuseki

# Run a specific repo standalone
standalone-kgb:
	cd repos/KnowledgeGraphBuilder && docker compose up -d

standalone-qa:
	cd repos/GraphQAAgent && docker compose up -d

standalone-onto:
	cd repos/OntologyExtender && docker compose up -d
