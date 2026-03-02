#!/usr/bin/env bash
set -euo pipefail

echo "=== KGPlatform Bootstrap ==="
echo ""
echo "This sets up KGPlatform for one-command deployment."
echo "All services, infrastructure, and models in a single docker compose."
echo ""

# 1. Initialize and clone submodules
echo "[1/4] Initializing git submodules..."
git submodule update --init --recursive

# 2. Create .env from example
if [[ ! -f .env ]]; then
    echo "[2/4] Creating .env from .env.example..."
    cp .env.example .env
    echo "  → Edit .env to change model names or passwords"
else
    echo "[2/4] .env already exists, skipping"
fi

# 3. Pull Docker images
echo "[3/4] Pulling Docker images..."
docker compose pull neo4j qdrant fuseki \
    ollama-kgbuilder ollama-graphqa ollama-ontology 2>/dev/null || true

# 4. Build all service images
echo "[4/4] Building service images..."
docker compose build

echo ""
echo "=== Bootstrap complete! ==="
echo ""
echo "Start everything with:"
echo "  docker compose up -d"
echo "  (or: make up)"
echo ""
echo "Models (qwen3:8b, qwen3-embedding) are pulled automatically on first start."
echo "Frontend: http://localhost:8501"
echo ""
