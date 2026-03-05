# KGPlatform — Implementation Consolidation

**Date**: March 2, 2026  
**Status**: Scaffolding Complete + Submodule FastAPI Wired  
**Important**: DO NOT kill existing containers. Wire to them instead.

---

## What We Have

### 1. KGPlatform Meta-Repository (this repo)
- **docker-compose.yml** — Orchestrates all services
- **Services**:
  - `kgbuilder-api:8001` → delegates to `kgbuilder.api.server:app` (from fast-api branch)
  - `graphqa-api:8002` → delegates to `kgrag.api.server:app` (from dev/fast-api-backend branch)
  - `ontology-api:8003` → custom FastAPI wrapper (OntologyExtender has no server.py)
  - `frontend:8501` → Streamlit UI
- **Shared Infrastructure**:
  - `neo4j:7687` (Bolt) + `7474` (browser)
  - `qdrant:6333`
  - `fuseki:3030`
  - `ollama-kgbuilder:11434` (ext port 11435)
  - `ollama-graphqa:11434` (ext port 11436)
  - `ollama-ontology:11434` (ext port 11437)

### 2. Existing Standalone Containers (DO NOT KILL)
Each repo has its own docker-compose.yml running independently:
- **KnowledgeGraphBuilder** — `repos/KnowledgeGraphBuilder/docker-compose.yml`
  - Runs its own `kgbuilder-api:8001` + neo4j + qdrant + fuseki + ollama
- **GraphQAAgent** — `repos/GraphQAAgent/docker-compose.yml`
  - Runs its own `graphqa-api:8002` + neo4j + qdrant + fuseki + ollama
- **OntologyExtender** — `repos/OntologyExtender/docker-compose.yml` (if exists)
  - Runs its own services

---

## The Problem

If both KGPlatform and the individual repos try to start containers on the same ports (8001, 8002, 8003), we get port conflicts.

---

## The Solution: Coexistence Strategy

### Option A: **Keep Repos Standalone, Use KGPlatform for Orchestration Only**
- **Keep running**: Individual repo containers (on original ports/networks)
- **KGPlatform role**: Provides shared infra (Neo4j, Qdrant, Fuseki) + wiring layer
- **How**: Modify KGPlatform docker-compose.yml to:
  1. Remove service definitions for kgbuilder-api, graphqa-api, ontology-api
  2. Keep only shared infra (neo4j, qdrant, fuseki, ollama)
  3. Keep only frontend:8501
  4. Frontend & services reference external APIs via environment variables

### Option B: **Replace Standalone Containers with KGPlatform**
- **Kill**: Individual repo containers
- **Start**: Single `docker compose up` from KGPlatform root
- **Pro**: Single source of truth, coordinated
- **Con**: Loosely integrated repos are tightly coupled

---

## Recommended: Option A

Keep the existing containers. Wire KGPlatform as a **thin orchestration layer** that:

1. **Provides shared infrastructure** (neo4j, qdrant, fuseki, ollama instances)
2. **Provides unified Streamlit frontend** (8501) → references the already-running APIs
3. **Provides health checking** script that verifies all services
4. **Each repo continues** operating independently on their own network/ports

### Implementation Steps

#### Step 1: Update KGPlatform docker-compose.yml
Remove the service definitions, keep only shared infra:

```yaml
version: "3.8"
services:
  # ⚠️  COMMENTED OUT — repos run standalone
  # kgbuilder-api:  ...
  # graphqa-api:   ...
  # ontology-api:  ...
  
  # Frontend talks to already-running services
  frontend:
    build: ./frontend
    ports: ["8501:8501"]
    environment:
      - KGBUILDER_API_URL=http://kgbuilder-api:8001
      - GRAPHQA_API_URL=http://graphqa-api:8002
      - ONTOLOGY_API_URL=http://ontology-api:8003
    # ... rest
```

#### Step 2: Update Health Check Script
```bash
scripts/health_check.sh
- Check KGBuilder:    http://localhost:8001/health
- Check GraphQA:      http://localhost:8002/health
- Check Ontology:     http://localhost:8003/health
- Check Streamlit:    http://localhost:8501
- Check Neo4j:        http://localhost:7474
- Check Qdrant:       http://localhost:6333
- Check Fuseki:       http://localhost:3030
```

#### Step 3: Environment Setup
- Frontend container must be able to resolve `kgbuilder-api:8001`, `graphqa-api:8002`, `ontology-api:8003`
  - If repos on same Docker network: ✅ works
  - If repos in separate networks: Use `host.docker.internal:8001` or network aliases

---

## Current Wiring Status

| Component | Status | Details |
|-----------|--------|---------|
| KGB FastAPI | ✅ Ready | `fast-api` branch, `kgbuilder.api.server:app` |
| GraphQA FastAPI | ✅ Ready | `dev/fast-api-backend` branch, `kgrag.api.server:app` |
| Ontology Wrapper | ✅ Ready | Custom wrapper in `services/ontology_api/` |
| Streamlit Frontend | ✅ Ready | `frontend/app.py` + 4 pages |
| Shared Schemas | ✅ Ready | `services/shared/schemas.py` + `client.py` |
| Docker Compose | ⚠️  Needs Update | Remove service defs, keep infra only |
| Health Script | ✅ Ready | `scripts/health_check.sh` |

---

## Recommendations

### **Short-term** (Now)
1. Keep all existing containers running
2. Update KGPlatform docker-compose to NOT start kgbuilder/graphqa/ontology services
3. Update KGPlatform docker-compose to start ONLY shared infra + frontend
4. Test that Streamlit frontend can call existing APIs

### **Medium-term** (After validation)
- Add inter-service wiring (gap detection feedback loop)
- Test HITL flow end-to-end
- Verify all 4 Streamlit pages work with live services

### **Long-term** (Optional consolidation)
- If all repos stable, migrate to single KGPlatform docker-compose
- Requires coordination (which repo's branch is canonical, etc.)

---

## Next Action

**Modify `docker-compose.yml`** to be a "meta-compose" that:
- ✅ Starts shared infrastructure ONLY (Neo4j, Qdrant, Fuseki, Ollama)
- ✅ Starts Streamlit frontend (references external APIs)
- ❌ Does NO start kgbuilder-api, graphqa-api, ontology-api
- 🔍 Let's the individual repos keep their own docker-compose files and containers

This avoids port conflicts while providing a unified orchestration point.
