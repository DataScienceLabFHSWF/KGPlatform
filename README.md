# KGPlatform

Meta-repository that orchestrates **KnowledgeGraphBuilder**, **GraphQAAgent**, and **OntologyExtender** into a unified Docker Compose deployment with FastAPI service layers.

## Architecture

```
                    ┌───────────────────────────────────────────┐
                    │            KGPlatform Network              │
                    │                                           │
  ┌─────────────┐  │  ┌──────────────┐  ┌──────────────────┐  │
  │  Streamlit   │──┼─►│ kgbuilder-api│  │  graphqa-api     │  │
  │  Frontend    │  │  │  :8001       │  │  :8002           │  │
  │  :8501       │──┼─►│              │  │                  │  │
  └─────────────┘  │  └──────┬───────┘  └────────┬─────────┘  │
                    │         │                    │            │
                    │         ▼                    ▼            │
                    │  ┌──────────────┐                         │
                    │  │ ontology-api │                         │
                    │  │  :8003       │                         │
                    │  └──────┬───────┘                         │
                    │         │                                 │
                    │  ═══════╪═════════════════════════════    │
                    │  Infrastructure (shared)                  │
                    │  Neo4j · Qdrant · Fuseki · Ollama         │
                    └───────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone with submodules
git clone --recurse-submodules https://github.com/DataScienceLabFHSWF/KGPlatform.git
cd KGPlatform

# 2. Bootstrap (creates .env, pulls images, builds services)
make bootstrap

# 3. Start everything
make up

# 4. Check health
make health
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| KGBuilder API | http://localhost:8001/docs | KG construction, validation, export |
| GraphQA API | http://localhost:8002/docs | Ontology-informed GraphRAG QA |
| Ontology API | http://localhost:8003/docs | Human-in-the-loop ontology extension |
| Frontend | http://localhost:8501 | Streamlit UI |
| Neo4j | http://localhost:7474 | Graph database browser |
| Qdrant | http://localhost:6333/dashboard | Vector store dashboard |
| Fuseki | http://localhost:3030 | SPARQL endpoint |

## HITL Feedback Loop

```
GraphQAAgent ──(low confidence)──► KGBuilder ──(gaps)──► OntologyExtender
     ▲                                 ▲                        │
     │                                 │                        │
     └── new CQs from users    expert corrections      updated OWL + SHACL
```

## Repository Structure

```
KGPlatform/
├── docker-compose.yml          # Full orchestrated deployment
├── .env.example                # Environment variables template
├── .gitmodules                 # Submodule definitions
├── Makefile                    # Convenience targets
├── repos/                      # Git submodules
│   ├── KnowledgeGraphBuilder/
│   ├── GraphQAAgent/
│   └── OntologyExtender/
├── services/                   # FastAPI wrappers
│   ├── kgbuilder_api/
│   ├── ontology_api/
│   ├── graphqa_api/
│   └── shared/                 # Shared schemas & client
├── frontend/                   # Streamlit UI
├── data/                       # Persistent data volumes
└── scripts/                    # Bootstrap & utility scripts
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make bootstrap` | Initialize submodules, create `.env`, pull images |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Follow service logs |
| `make health` | Check all service health endpoints |
| `make build` | Rebuild service images |
| `make infra` | Start infrastructure only (Neo4j, Qdrant, Fuseki) |
| `make standalone-kgb` | Run KnowledgeGraphBuilder standalone |
| `make standalone-qa` | Run GraphQAAgent standalone |
| `make standalone-onto` | Run OntologyExtender standalone |

## Environment Variables

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

Key variables:
- `NEO4J_USER` / `NEO4J_PASSWORD` — Neo4j credentials
- `FUSEKI_ADMIN_PASSWORD` — Fuseki admin password
- `KGBUILDER_MODEL` / `GRAPHQA_MODEL` / `ONTOLOGY_MODEL` — Ollama model per service
- `LOG_LEVEL` — Logging level (INFO, DEBUG, etc.)

## License

See [LICENSE](LICENSE).
