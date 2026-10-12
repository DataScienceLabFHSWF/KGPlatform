#!/usr/bin/env sh
# Gets the upstream LLM Graph Builder code at a fixed version and creates .env.
# Safe to run again: it skips steps that are already done.
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

[ -f .env ] || { cp .env.example .env; echo "Created .env - fill in KG_OLLAMA_MODEL and KG_NEO4J_PASSWORD."; }

# Read the tag from .env so compose and the checkout always match.
TAG="$(grep -E '^KG_UPSTREAM_TAG=' .env | cut -d= -f2)"
TAG="${TAG:-v0.8.7}"

if [ -d upstream/.git ]; then
    echo "upstream/ already exists at: $(git -C upstream describe --tags 2>/dev/null || echo unknown)"
    echo "To change version: delete upstream/ and run this script again."
else
    git clone --depth 1 --branch "$TAG" https://github.com/neo4j-labs/llm-graph-builder.git upstream
fi

echo "Next: podman-compose up -d --build   (or: docker compose up -d --build)"
