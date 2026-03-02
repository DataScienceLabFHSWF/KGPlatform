#!/usr/bin/env bash
set -euo pipefail

echo "=== KGPlatform Bootstrap ==="

# 1. Initialize and clone submodules
echo "[1/5] Initializing git submodules..."
git submodule update --init --recursive

# 2. Create .env from example
if [[ ! -f .env ]]; then
    echo "[2/5] Creating .env from .env.example..."
    cp .env.example .env
    echo "  → Edit .env with your settings before starting"
else
    echo "[2/5] .env already exists, skipping"
fi

# 3. Create data directories
echo "[3/5] Creating data directories..."
mkdir -p data/{neo4j,qdrant,fuseki,ontology,shared/change_requests}

# 4. Pull Docker images
echo "[4/5] Pulling Docker images..."
docker compose pull neo4j qdrant fuseki ollama-kgbuilder ollama-graphqa ollama-ontology

# 5. Build service images
echo "[5/5] Building service images..."
docker compose build kgbuilder-api graphqa-api ontology-api frontend

echo ""
echo "=== Bootstrap complete! ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env if needed"
echo "  2. docker compose up -d                    # start everything"
echo "  3. docker compose logs -f                  # watch logs"
echo "  4. Open http://localhost:8501               # Streamlit frontend"
echo "  5. API docs:"
echo "     - KGBuilder:   http://localhost:8001/docs"
echo "     - GraphQA:     http://localhost:8002/docs"
echo "     - Ontology:    http://localhost:8003/docs"
