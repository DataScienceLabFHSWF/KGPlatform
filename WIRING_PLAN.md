# KGPlatform ↔ Standalone Repo Wiring Plan

## Current Architecture

KGPlatform's `docker-compose.yml` runs **shared infrastructure only**:

| Container             | Image                  | Port(s)        | Volume (bind-mount source)                                  |
|-----------------------|------------------------|----------------|-------------------------------------------------------------|
| `kgplatform-neo4j`    | neo4j:5.26.0           | 7474, 7687     | `/home/fneubuerger/KnowledgeGraphBuilder/data/neo4j`        |
| `kgplatform-qdrant`   | qdrant/qdrant:latest   | 6333           | `/home/fneubuerger/KnowledgeGraphBuilder/data/qdrant`       |
| `kgplatform-fuseki`   | stain/jena-fuseki      | 3030           | `/home/fneubuerger/KnowledgeGraphBuilder/data/fuseki`       |
| `ollama-kgbuilder`    | ollama/ollama:0.14.3   | 18134→11434    | Docker volume `ollama-kgbuilder-data`                       |
| `ollama-graphqa`      | ollama/ollama:0.14.3   | 18136→11434    | Docker volume `ollama-graphqa-data`                         |
| `ollama-ontology`     | ollama/ollama:0.14.3   | 18135→11434    | Docker volume `ollama-ontology-data`                        |
| `kgplatform-frontend` | kgplatform-frontend    | 8501           | (none)                                                      |

The **API services** run from within their respective repos, either:
- **Option A**: Locally with `uvicorn` (for development)
- **Option B**: Via each repo's `docker-compose.yml` (API-only, no infra)

---

## What Needs to Change in Each Repo

### 1. KnowledgeGraphBuilder (port 8001)

**Problem**: Its `docker-compose.yml` defines its own `neo4j`, `qdrant`, `fuseki`, `ollama` containers, which conflict with KGPlatform's.

**Solution**: Create a `.env` file that points to KGPlatform's exposed ports on `localhost`:

```env
# .env — points to KGPlatform infrastructure (running on host ports)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=kgbuilder
FUSEKI_URL=http://localhost:3030
FUSEKI_DATASET=kgbuilder
OLLAMA_URL=http://localhost:18134
OLLAMA_MODEL=qwen3:8b
```

**To run API only** (no infra containers):
```bash
cd repos/KnowledgeGraphBuilder
uvicorn kgbuilder.api.server:app --host 0.0.0.0 --port 8001
```

Or use a slim compose override that builds only `kgbuilder-api` with `network_mode: host`.

---

### 2. GraphQAAgent (port 8002)

**Problem**: Its `docker-compose.yml` defines its own `neo4j` (with password `password`!), `qdrant`, `fuseki`, `ollama` — all conflicting.

**Solution**: Create a `.env` file with KGPlatform-compatible settings:

```env
# .env — points to KGPlatform infrastructure
KGRAG_NEO4J__URI=bolt://localhost:7687
KGRAG_NEO4J__USER=neo4j
KGRAG_NEO4J__PASSWORD=changeme          # ← was "password" in standalone!
KGRAG_NEO4J__DATABASE=neo4j
KGRAG_QDRANT__URL=http://localhost:6333
KGRAG_QDRANT__COLLECTION_NAME=kgbuilder
KGRAG_FUSEKI__URL=http://localhost:3030
KGRAG_FUSEKI__DATASET=kgbuilder
KGRAG_OLLAMA__BASE_URL=http://localhost:18136
KGRAG_OLLAMA__GENERATION_MODEL=qwen3:8b
KGRAG_OLLAMA__EMBEDDING_MODEL=qwen3-embedding:latest
KGRAG_OLLAMA__TEMPERATURE=0.3
KGRAG_OLLAMA__MAX_TOKENS=4096
KGRAG_API_PORT=8002
KGRAG_CORS_ORIGINS=http://localhost:8501,http://localhost:3000
KGRAG_LOG_LEVEL=INFO
```

**Critical change**: Neo4j password `password` → `changeme`

**To run API only**:
```bash
cd repos/GraphQAAgent
uvicorn kgrag.api.server:app --host 0.0.0.0 --port 8002
```

---

### 3. OntologyExtender (port 8003)

**Problem**: Its `docker-compose.yml` defines its own `fuseki`, `ollama-ontology`, plus legacy containers.

**Solution**: Create a `.env` file pointing to KGPlatform:

```env
# .env — points to KGPlatform infrastructure
HITL_FUSEKI_URL=http://localhost:3030
HITL_FUSEKI_DATASET=kgbuilder
HITL_FUSEKI_STAGING_DATASET=kgbuilder-staging
HITL_FUSEKI_USER=admin
HITL_FUSEKI_PASSWORD=admin
HITL_QDRANT_URL=http://localhost:6333
HITL_QDRANT_COLLECTION=kgbuilder
HITL_OLLAMA_URL=http://localhost:18135
HITL_OLLAMA_MODEL=qwen3:8b
KGBUILDER_API_URL=http://localhost:8001
```

**To run API only**:
```bash
cd repos/OntologyExtender
uvicorn ontology_hitl.api.server:app --host 0.0.0.0 --port 8003
```

---

## Summary of Breaking Changes

| Repo              | Key Change                                       | Impact                       |
|-------------------|--------------------------------------------------|------------------------------|
| GraphQAAgent      | Neo4j password `password` → `changeme`           | **Breaking** if not updated  |
| GraphQAAgent      | Ollama URL `11434` → `18136`                     | Uses dedicated Ollama        |
| KnowledgeGraphBuilder | Ollama URL `11435` → `18134`                 | Uses dedicated Ollama        |
| OntologyExtender  | Ollama URL `11437` → `18135`                     | Uses dedicated Ollama        |
| All repos         | Stop starting infra containers (neo4j, qdrant…)  | Use KGPlatform's instances   |

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│  KGPlatform docker-compose (kgplatform network)                │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Neo4j    │  │ Qdrant   │  │ Fuseki   │  │ 3× Ollama      │  │
│  │ :7474    │  │ :6333    │  │ :3030    │  │ :18134/135/136 │  │
│  │ :7687    │  │          │  │          │  │                │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│                                                                 │
│  ┌──────────────────┐                                           │
│  │ Streamlit :8501  │  (references APIs via env vars)           │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
        ↕ host ports ↕
┌──────────┐  ┌──────────┐  ┌──────────┐
│ KGB API  │  │ GraphQA  │  │ Ontology │
│ :8001    │  │ :8002    │  │ :8003    │
│ (local)  │  │ (local)  │  │ (local)  │
└──────────┘  └──────────┘  └──────────┘
```

Services run locally (not in Docker) and connect to KGPlatform infra via `localhost` ports.
