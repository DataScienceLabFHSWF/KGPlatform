# KGPlatform Integration & Wiring Guide

## Overview

KGPlatform is a **meta-repository** that orchestrates three research repos via Docker Compose:
- **KnowledgeGraphBuilder** (fast-api branch) → runs `kgbuilder.api.server:app`
- **GraphQAAgent** (dev/fast-api-backend branch) → runs `kgrag.api.server:app`  
- **OntologyExtender** (main) → runs our wrapper `services/ontology_api/main:app`

All three are deployed **independently** with their own Ollama instances but share Neo4j/Qdrant/Fuseki infrastructure.

---

## Architecture Layers

```
┌─────────────────────────────────────┐
│      Streamlit Frontend (8501)      │
│    (health checks, UI for all 3)    │
└──────────┬──────────────┬───────────┘
           │              │
      ┌────▼─────┐   ┌────▼──────┐   ┌─────────────┐
      │ kgbuilder │   │  graphqa  │   │  ontology   │
      │   -api   │   │   -api     │   │    -api     │
      │(8001)    │   │  (8002)    │   │  (8003)     │
      └────┬────┘    └────┬──────┘   └──────┬──────┘
           │              │                 │
      ┌────┴──────────────┴─────────────────┴──────┐
      │   Shared Infrastructure Network            │
      │   neo4j:7687 | qdrant:6333 | fuseki:3030  │
      │   ollama-kgbuilder:11434                   │
      │   ollama-graphqa:11434                     │
      │   ollama-ontology:11434                    │
      └────────────────────────────────────────────┘
```

---

## Dockerfile Strategy

### KGBuilder & GraphQA: Delegation
These repos have native FastAPI implementations on their fast-api branches.

**Dockerfile approach:**
```dockerfile
# Copy the entire repo (which is on the fast-api branch)
COPY repos/KnowledgeGraphBuilder/ /app
RUN pip install -e /app

# Run the native server.py
CMD ["uvicorn", "kgbuilder.api.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### OntologyExtender: Wrapper
OntologyExtender doesn't have a native FastAPI server yet, so we provide a thin wrapper.

**Dockerfile approach:**
```dockerfile
# Install OntologyExtender as a library
COPY repos/OntologyExtender/ /app
RUN pip install -e /app

# Copy our wrapper routes
COPY services/ontology_api/ /app/service/
WORKDIR /app/service

# Run our custom main.py which imports from ontology_hitl
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
```

---

## Service-to-Service Communication

### Health Checks
```bash
# Frontend checks these on page load:
curl http://kgbuilder-api:8001/api/v1/health
curl http://graphqa-api:8002/api/v1/health
curl http://ontology-api:8003/api/v1/health
```

### HITL Feedback Loop
```
GraphQA (8002)
  ├─ POST /api/v1/hitl/report-low-confidence
  └─► KGBuilder (8001)
       ├─ POST /api/v1/hitl/gaps/detect
       └─► OntologyExtender (8003)
            ├─ POST /api/v1/extend
            └─► Update Fuseki ontology
```

### Environment Variables
Each service connects to shared infrastructure via env:
```bash
NEO4J_URI=bolt://neo4j:7687
QDRANT_URL=http://qdrant:6333
FUSEKI_URL=http://fuseki:3030
OLLAMA_URL=http://ollama-{service}:11434
```

---

## Deployment Modes

### Mode 1: Full Stack (from KGPlatform root)
**When:** Local development, testing full platform

```bash
docker compose up -d
# Starts:
#   - All 3 app services + frontend
#   - All infrastructure (neo4j, qdrant, fuseki)
#   - 3 x Ollama instances
```

**Pros:**
- Isolated environment
- No port conflicts with existing services
- Self-contained for testing

**Cons:**
- Requires significant resources (3 Ollama containers)
- Duplicates infrastructure already running elsewhere

### Mode 2: Standalone Submodule (legacy)
**When:** Developing one repo in isolation

```bash
cd repos/KnowledgeGraphBuilder
docker compose up -d
# Uses the repo's own docker-compose.yml
# Starts its own Neo4j, Qdrant, Fuseki, Ollama
```

**Pros:**
- Independent development per repo
- Isolated from other work

**Cons:**
- Duplicates infrastructure
- No inter-service communication

---

## Wiring Decisions Made

### ✅ What We Did
1. **Checked out fast-api branches** in KGB and GraphQA
   - These branches have complete FastAPI implementations
   - No wrapper needed, just delegate to their server.py

2. **Created OntologyExtender wrapper** in `/services/ontology_api/`
   - OntologyExtender doesn't have native FastAPI yet
   - Our wrapper provides compatible API surface
   - Imports from `ontology_hitl.*` core logic

3. **Shared infrastructure** via docker-compose
   - All 3 services talk to same Neo4j, Qdrant, Fuseki
   - Each has its own Ollama for model isolation
   - Easy to extend: add more services without changing infrastructure

4. **Clear health check endpoints**
   - Each service: `GET /api/v1/health`
   - Frontend uses these for status badges
   - Essential for debugging HITL loops

### ❌ What We Avoided
- **Port conflicts**: Each service on unique port (8001/8002/8003)
- **Package duplication**: Repos installed as `-e` (editable) from their actual code
- **Wrapper complexity**: KGB & GraphQA delegate directly, no extra middleware
- **Breaking existing containers**: All new deployment is in `kgplatform` Docker network

---

## Testing & Validation

### Quick health check
```bash
make health
```

### Full integration test
1. Build services: `docker compose build`
2. Start platform: `docker compose up -d`
3. Check services online
4. Test HITL loop:
   ```bash
   # Report low-confidence from GraphQA
   curl -X POST http://localhost:8002/api/v1/hitl/report-low-confidence \
     -H "Content-Type: application/json" \
     -d '{"qa_results": [{"question": "test", "confidence": 0.1}]}'
   
   # Should trigger gap detection in KGB
   curl http://localhost:8001/api/v1/hitl/gaps
   ```

---

## Submodule Branch Status

| Repo | Current Branch | FastAPI Impl | Status |
|------|---|---|---|
| **KnowledgeGraphBuilder** | `fast-api` | ✅ `kgbuilder.api.server:app` | Ready to deploy |
| **GraphQAAgent** | `dev/fast-api-backend` | ✅ `kgrag.api.server:app` | Ready to deploy |
| **OntologyExtender** | `main` | ⚠️ Wrapper only | Wrapper in `/services/ontology_api/` |

---

## Clean Integration Workflow

```bash
# 1. Start fresh (ensure no legacy containers interfere)
docker ps -a | grep -E "(neo4j|qdrant|fuseki|ollama)" # Check for conflicts

# 2. Build KGPlatform services
cd /home/fneubuerger/KGPlatform
docker compose build

# 3. Start entire platform
docker compose up -d

# 4. Verify health
make health

# 5. Access services
# - Frontend: http://localhost:8501
# - KGB docs: http://localhost:8001/docs
# - GraphQA docs: http://localhost:8002/docs
# - Ontology docs: http://localhost:8003/docs
```

---

## Future: Running Main+Fast-api Together

Once all 3 repos have stable FastAPI implementations:

1. **Update submodule branches to main** (when fast-api is merged)
2. **No Dockerfile changes needed** — delegation already works
3. **Services automatically use latest** — just pull and rebuild
4. **HITL loops fully tested** — cross-service communication ready

---

## Key Files

- [docker-compose.yml](../docker-compose.yml) — Service definitions & networking
- [services/kgbuilder_api/Dockerfile](../services/kgbuilder_api/Dockerfile) — Delegates to KGB
- [services/graphqa_api/Dockerfile](../services/graphqa_api/Dockerfile) — Delegates to GraphQA
- [services/ontology_api/](../services/ontology_api/) — Wrapper for OntologyExtender
- [services/shared/schemas.py](../services/shared/schemas.py) — Cross-service data models
- [scripts/bootstrap.sh](../scripts/bootstrap.sh) — One-command setup

