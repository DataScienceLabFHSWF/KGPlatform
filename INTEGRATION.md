# KGPlatform Integration Guide

## Architecture

KGPlatform integrates three research repositories into a single orchestrated ecosystem through FastAPI service layers and Docker Compose orchestration.

### Submodule FastAPI Implementations

| Service | Repo | Branch | Server | Port | Ollama Port |
|---------|------|--------|--------|------|-------------|
| **KGBuilder** | `KnowledgeGraphBuilder` | `fast-api` | `kgbuilder.api.server:app` | 8001 | 18134 |
| **GraphQA** | `GraphQAAgent` | `dev/fast-api-backend` | `kgrag.api.server:app` | 8002 | 18136 |
| **OntologyExtender** | `OntologyExtender` | `main` | `services/ontology_api/main:app` (wrapper) | 8003 | 18135 |

### Shared Infrastructure

```
┌─────────────────────────────────────────────────┐
│  Shared Docker Network: "kgplatform"            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Neo4j (7474/7687)   ← Graph Database          │
│  Qdrant (6333)       ← Vector Store            │
│  Fuseki (3030)       ← RDF/SPARQL Endpoint     │
│                                                 │
│  ollama-kgbuilder (18134)                      │
│  ollama-graphqa (18136)                        │
│  ollama-ontology (18135)                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Port Mappings

### Service APIs

```
localhost:8001  → KGBuilder FastAPI (docs at /docs)
localhost:8002  → GraphQA FastAPI (docs at /docs)
localhost:8003  → OntologyExtender FastAPI (docs at /docs)
localhost:8501  → Streamlit Frontend
```

### Infrastructure

```
localhost:7474  → Neo4j Browser
localhost:7687  → Neo4j Bolt (driver)
localhost:6333  → Qdrant Vector Store
localhost:3030  → Fuseki SPARQL Endpoint
```

### Ollama (Model Serving)

```
localhost:18134  → ollama-kgbuilder (extraction models)
localhost:18136  → ollama-graphqa (QA models)
localhost:18135  → ollama-ontology (reasoning models)
```

## Dockerfile Strategy

### For KGBuilder & GraphQA

The Dockerfiles **delegate directly** to the submodule implementations:

```dockerfile
FROM python:3.11-slim
COPY repos/<repo>/ /app
RUN pip install -e /app
CMD ["uvicorn", "<module>.api.server:app", "--host", "0.0.0.0", "--port", "<port>"]
```

### For OntologyExtender (No Existing Server)

We provide a **thin FastAPI wrapper** that imports the OntologyExtender logic:

```dockerfile
FROM python:3.11-slim
COPY repos/OntologyExtender/ /app
COPY services/ontology_api/ /app/service/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
```

## Branch Checkout

All submodules are checked out to their respective API-ready branches:

```bash
cd repos/KnowledgeGraphBuilder && git checkout fast-api
cd repos/GraphQAAgent && git checkout dev/fast-api-backend
cd repos/OntologyExtender && git checkout main
```

## Inter-Service Communication

Services communicate **directly via HTTP** on the shared Docker network:

```
GraphQAAgent (8002)
    ↓ (low confidence)
KGBuilder (8001)
    ↓ (gaps)
OntologyExtender (8003)
    ↓ (updated ontology)
Back to KGBuilder
```

### Example: GraphQA → KGBuilder Gap Detection

```python
# Trigger from GraphQA HITL endpoint
POST http://kgbuilder-api:8001/api/v1/hitl/gaps/detect
{
  "qa_results": [...]
}
```

## Shared Schemas

All inter-service communication uses **canonical Pydantic models** defined in [`services/shared/schemas.py`](services/shared/schemas.py):

- `QAQuestion` — Competency questions
- `GapReport` — Gap detection results
- `TBoxChangeRequest` — Ontology change requests
- `EntitySummary`, `RelationSummary` — KG entities

## Wiring (No Wrapper Overhead)

**Zero wrapper overhead** — services directly expose their native FastAPI servers, making debugging and development straightforward:

```
docker-compose → Dockerfile → pip install -e /app → uvicorn <real server>
                                    ↓
                        (Submodule's actual implementation)
```

## Environment Variables

All services read from `.env`:

```bash
# Neo4j
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme

# Fuseki
FUSEKI_ADMIN_PASSWORD=admin

# Ollama Models
KGBUILDER_MODEL=qwen3:8b
GRAPHQA_MODEL=qwen3:8b
ONTOLOGY_MODEL=qwen3:8b

# Service URLs (auto-resolved in Docker)
OLLAMA_URL=http://ollama-<service>:11434
NEO4J_URI=bolt://neo4j:7687
QDRANT_URL=http://qdrant:6333
FUSEKI_URL=http://fuseki:3030
```

## Quick Start

```bash
# 1. Clone with branches already set
git clone <repo>
cd KGPlatform

# 2. Create .env
cp .env.example .env

# 3. Start shared infrastructure + all services
docker compose up -d

# 4. Check health
docker compose ps
curl http://localhost:8001/api/v1/health
curl http://localhost:8002/api/v1/health
curl http://localhost:8003/api/v1/health
```

## Debugging

### View logs for a service

```bash
docker compose logs -f kgbuilder-api
docker compose logs -f graphqa-api
docker compose logs -f ontology-api
```

### Access FastAPI docs

- KGBuilder: http://localhost:8001/docs
- GraphQA: http://localhost:8002/docs
- OntologyExtender: http://localhost:8003/docs (swagger auto-gen from routes)

### Check Neo4j

```bash
# Browser
http://localhost:7474

# Cypher queries
neo4j@neo4j/changeme
```

### Query Fuseki SPARQL

```bash
curl http://localhost:3030/kgbuilder/sparql \
  -d "query=SELECT * WHERE { ?s ?p ?o } LIMIT 10"
```

## Build & Deployment

### Build specific service

```bash
docker compose build kgbuilder-api
docker compose build graphqa-api
docker compose build ontology-api
```

### Build all

```bash
docker compose build
```

### Push to registry

```bash
docker tag kgplatform-kgbuilder-api <registry>/kgbuilder-api:latest
docker push <registry>/kgbuilder-api:latest
```

## Notes

- **Submodule updates**: Pull changes with `git submodule update --remote`
- **Port conflicts**: Uses 1813X range for Ollama to avoid colleague collisions
- **Coexistent deployment**: Can run alongside existing containers (Kiko, HITL Fuseki, etc.)
- **Zero wrapper overhead**: Direct delegation to submodule implementations

---

**Last updated**: 2026-03-02
