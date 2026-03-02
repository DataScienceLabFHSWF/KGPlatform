#!/usr/bin/env bash
set -euo pipefail

echo "=== KGPlatform Health Check ==="

services=(
    "KGBuilder|http://localhost:8001/api/v1/health"
    "GraphQA|http://localhost:8002/api/v1/health"
    "Ontology|http://localhost:8003/api/v1/health"
    "Neo4j|http://localhost:7474"
    "Qdrant|http://localhost:6333/dashboard"
    "Fuseki|http://localhost:3030"
    "Frontend|http://localhost:8501"
)

all_ok=true

for entry in "${services[@]}"; do
    name="${entry%%|*}"
    url="${entry##*|}"
    if curl -sf --max-time 3 "$url" > /dev/null 2>&1; then
        printf "  %-15s ✅ Online\n" "$name"
    else
        printf "  %-15s ❌ Offline\n" "$name"
        all_ok=false
    fi
done

echo ""
if $all_ok; then
    echo "All services are running!"
else
    echo "Some services are offline. Check: docker compose logs"
fi
