# KGPlatform

Orchestration repository that wires **KnowledgeGraphBuilder**, **GraphQAAgent**, and **OntologyExtender** into a single Docker Compose deployment. This repo contains no application logic — all development, benchmarking, and experimentation happens inside the individual submodule repositories.

| Repository | Purpose | Branch |
|-----------|---------|--------|
| [KnowledgeGraphBuilder](https://github.com/DataScienceLabFHSWF/KnowledgeGraphBuilder) | KG construction, validation, export | `fast-api` |
| [GraphQAAgent](https://github.com/DataScienceLabFHSWF/GraphQAAgent) | Ontology-informed GraphRAG QA | `dev/fast-api-backend` |
| [OntologyExtender](https://github.com/DataScienceLabFHSWF/OntologyExtender) | Human-in-the-loop ontology extension | `fast-api` |

> **Note:** The FastAPI branches are the active development branches. They will be merged to `main` once integration testing via this platform is complete. Each repo works standalone — KGPlatform just ties them together.

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
                    │  │  :8010       │                         │
                    │  └──────┬───────┘                         │
                    │         │                                 │
                    │  ═══════╪═════════════════════════════    │
                    │  Infrastructure (shared)                  │
                    │  Neo4j · Qdrant · Fuseki                  │
                    │  Ollama ×3 (auto model pull)              │
                    └───────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose v2
- NVIDIA GPU with drivers installed (for Ollama inference)
- ~25 GB disk for Ollama models (first run only)

### Setup

```bash
# 1. Clone with submodules
git clone --recurse-submodules https://github.com/DataScienceLabFHSWF/KGPlatform.git
cd KGPlatform

# 2. Create environment config
cp .env.example .env          # edit to change passwords or models

# 3. Start everything (builds images, pulls models automatically)
docker compose up -d --build

# 4. Verify all services
make health
```

One command brings up all infrastructure, pulls Ollama models, and starts three API services + a Streamlit frontend.

### What Happens on First Start

1. Docker builds three API images from the submodule Dockerfiles
2. Infrastructure containers start (Neo4j, Qdrant, Fuseki, 3× Ollama)
3. Three **init containers** pull the configured models (`qwen3:8b` + `qwen3-embedding`) into each Ollama instance — this takes 5–10 min on first run, is a no-op if models already exist
4. API services start once their init container exits successfully
5. Frontend starts once all APIs are up

## Services & Port Map

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| KGBuilder API | 8001 | http://localhost:8001/docs | KG construction, validation, export |
| GraphQA API | 8002 | http://localhost:8002/docs | Ontology-informed GraphRAG QA |
| Ontology API | 8010 | http://localhost:8010/docs | Human-in-the-loop ontology extension |
| Frontend | 8501 | http://localhost:8501 | Streamlit UI (Build KG, QA Chat, Ontology, Review) |
| Neo4j | 7474 | http://localhost:7474 | Graph database browser (bolt: 7687) |
| Qdrant | 6333 | http://localhost:6333/dashboard | Vector store dashboard |
| Fuseki | 3030 | http://localhost:3030 | SPARQL endpoint |

### Ollama Instances

Each API service gets its own Ollama. Models are pulled automatically on first `docker compose up` via init containers.

| Instance | Host Port | Models | Used By |
|----------|-----------|--------|---------|
| ollama-kgbuilder | 18134 | qwen3:8b, qwen3-embedding | KGBuilder API |
| ollama-graphqa | 18136 | qwen3:8b, qwen3-embedding | GraphQA API |
| ollama-ontology | 18135 | qwen3:8b | Ontology API |

## Standalone vs Platform

Each submodule can run independently or as part of KGPlatform. This is important because **all benchmarking, experiments, and active development happen in the individual repos** — KGPlatform just provides the orchestrated deployment for integration testing and the combined frontend.

| Mode | Where | Command | What You Get |
|------|-------|---------|-------------|
| **Platform** | `KGPlatform/` | `docker compose up -d` | All 3 APIs + shared infra + frontend |
| **KGB standalone** | `repos/KnowledgeGraphBuilder/` | `docker compose up -d` | Own Neo4j, Qdrant, Fuseki, Ollama |
| **GraphQA standalone** | `repos/GraphQAAgent/` | `docker compose up -d` | Own infra stack |
| **Ontology standalone** | `repos/OntologyExtender/` | `docker compose up -d` | Own Fuseki + Ollama |

Container names are namespaced to avoid collisions (`kgb-*`, `graphqa-*`, `ontology-*`, `kgplatform-*`), so you can run multiple stacks side by side if needed.

### Running Benchmarks & Experiments from Submodules

When you `cd` into a submodule directory, you work with that repo's own `docker-compose.yml`, its own `.env`, and its own Ollama instance. The platform compose is not involved.

**Example — OntologyExtender benchmarks:**

```bash
cd repos/OntologyExtender
cp .env.example .env

# Start standalone stack (Fuseki + Ollama + API)
docker compose up -d --build

# Pull additional models for benchmarking (into the standalone Ollama)
docker exec ontology-ollama ollama pull llama3.2:3b
docker exec ontology-ollama ollama pull nemotron-3-nano
docker exec ontology-ollama ollama pull qwen3-next:latest

# Run model comparison (overrides HITL_OLLAMA_MODEL per experiment)
python scripts/run_model_comparison.py \
    --experiments experiments/comprehensive_experiments.json \
    --output results/comprehensive.json

# Run OntoURL benchmark
python scripts/run_ontourl_benchmark.py --model llama3.2:3b

# Run debate strategy experiments
python scripts/run_experiments.py \
    --experiments experiments/small_model_experiments.json \
    --output results/small_model.json
```

**Example — KnowledgeGraphBuilder:**

```bash
cd repos/KnowledgeGraphBuilder
cp .env.example .env
docker compose up -d --build

# Run the full KG pipeline
python scripts/full_kg_pipeline.py --max-iterations 2

# Or use the API
curl -X POST http://localhost:8001/api/v1/build \
    -H "Content-Type: application/json" \
    -d '{"ontology_path": "data/ontology/plan-ontology-v1.0.owl", "document_dir": "data/documents"}'
```

**Example — GraphQA Agent:**

```bash
cd repos/GraphQAAgent
cp .env.example .env
docker compose up -d --build

# Chat via API
curl -X POST http://localhost:8002/api/v1/chat/send \
    -H "Content-Type: application/json" \
    -d '{"message": "What is nuclear decommissioning?", "strategy": "hybrid_sota"}'
```

> See each submodule's own README for full documentation of available scripts, benchmark procedures, and configuration options.

## Models Used Across the Ecosystem

| Model | Params | Role | Used In |
|-------|--------|------|---------|
| `qwen3:8b` | 8B | Default production model (reasoning) | All three APIs |
| `qwen3-embedding` | — | Embedding / semantic similarity | KGB, GraphQA, Ontology (fallback) |
| `llama3.2:3b` | 3.2B | Small non-reasoning baseline | OntologyExtender benchmarks |
| `nemotron-3-nano` | ~8B | Medium model experiments | OntologyExtender benchmarks |
| `qwen3-next` | 79.7B | Large reasoning model | OntologyExtender benchmarks |

The platform's `docker-compose.yml` pulls only `qwen3:8b` and `qwen3-embedding` automatically. Additional benchmark models must be pulled manually into the relevant Ollama instance (see benchmarking examples above).

## HITL Feedback Loop

The three services form a closed-loop system for iterative KG improvement:

```
GraphQAAgent ──(low confidence)──► KGBuilder ──(gaps)──► OntologyExtender
     ▲                                 ▲                        │
     │                                 │                        │
     └── new CQs from users    expert corrections      updated OWL + SHACL
```

1. **GraphQA** detects low-confidence answers or missing knowledge
2. **KGBuilder** runs gap analysis and identifies ontology coverage issues
3. **OntologyExtender** proposes extensions via multi-agent debate
4. A human reviewer accepts, rejects, or revises proposals
5. Extended ontology feeds back into the next KG build cycle

## Repository Structure

```
KGPlatform/
├── docker-compose.yml          # Full orchestrated deployment
├── .env / .env.example         # Environment variables
├── .gitmodules                 # Submodule definitions
├── Makefile                    # Convenience targets
├── repos/                      # Git submodules (each has own docker-compose.yml)
│   ├── KnowledgeGraphBuilder/  # KG construction pipeline
│   ├── GraphQAAgent/           # GraphRAG QA agent
│   └── OntologyExtender/       # HITL ontology extension
├── frontend/                   # Streamlit UI (platform-only)
│   ├── Dockerfile
│   ├── app.py                  # Home page with service health
│   └── pages/
│       ├── 1_Build_KG.py       # KG construction UI
│       ├── 2_QA_Chat.py        # Chat interface (streaming SSE)
│       ├── 3_Ontology.py       # Ontology browser
│       └── 4_Review.py         # HITL review workflow
└── scripts/
    ├── bootstrap.sh            # One-time setup
    └── health_check.sh         # Service health verification
```

## Makefile Targets

```
make up               Start everything (infra + APIs + frontend)
make down             Stop everything
make build            Build all service images
make logs             Follow logs
make health           Check all service health endpoints
make bootstrap        Initialize submodules, create .env, pull images
make infra            Start infrastructure only (Neo4j, Qdrant, Fuseki, Ollama)
make standalone-kgb   Run KnowledgeGraphBuilder standalone
make standalone-qa    Run GraphQAAgent standalone
make standalone-onto  Run OntologyExtender standalone
```

## Environment Variables

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `changeme` | Neo4j password |
| `FUSEKI_ADMIN_PASSWORD` | `admin` | Fuseki admin password |
| `FUSEKI_DATASET` | `kgbuilder` | Default Fuseki dataset |
| `QDRANT_COLLECTION` | `kgbuilder` | Qdrant collection name |
| `KGBUILDER_MODEL` | `qwen3:8b` | LLM for KGBuilder |
| `GRAPHQA_MODEL` | `qwen3:8b` | LLM for GraphQA |
| `ONTOLOGY_MODEL` | `qwen3:8b` | LLM for OntologyExtender |
| `EMBED_MODEL` | `qwen3-embedding` | Embedding model |
| `LOG_LEVEL` | `INFO` | Logging level |

## Troubleshooting

### Services show "unhealthy"

GraphQA loads its ontology context from Fuseki on startup, which can take 30–90 seconds. Wait for the start period to complete, then re-check:

```bash
make health
```

### Init containers keep re-pulling models

This is normal on first start. Model pulls are idempotent — if the model already exists in the Ollama volume, the pull finishes instantly.

### Port conflicts with other stacks

If you have other services (e.g. Kiko) running on conflicting ports, either stop them or change ports in `.env`. The standalone compose files use different default ports to avoid conflicts.

### Running platform + standalone simultaneously

Possible because container names are namespaced, but **be mindful of GPU memory** — each Ollama instance loads models into VRAM.

## License

See [LICENSE](LICENSE).
