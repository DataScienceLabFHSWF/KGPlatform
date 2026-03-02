#!/usr/bin/env bash
set -euo pipefail

echo "=== KGPlatform Health Check ==="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    if curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $name"
        return 0
    else
        echo -e "${RED}❌${NC} $name"
        return 1
    fi
}

check_ollama_models() {
    local name=$1
    local container=$2
    local models
    models=$(docker exec "$container" ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | tr '\n' ', ' | sed 's/,$//')
    if [[ -n "$models" ]]; then
        echo -e "${GREEN}✅${NC} $name  [${models}]"
    else
        echo -e "${YELLOW}⏳${NC} $name  (no models yet)"
    fi
}

echo "--- API Services ---"
check_service "KGBuilder API  :8001 " "http://localhost:8001/api/v1/health" || true
check_service "GraphQA API    :8002 " "http://localhost:8002/api/v1/health" || true
check_service "Ontology API   :8010 " "http://localhost:8010/api/v1/health" || true

echo ""
echo "--- Infrastructure ---"
check_service "Neo4j Browser  :7474 " "http://localhost:7474" || true
check_service "Qdrant         :6333 " "http://localhost:6333/healthz" || true
check_service "Fuseki         :3030 " "http://localhost:3030/$/ping" || true

echo ""
echo "--- Frontend ---"
check_service "Streamlit      :8501 " "http://localhost:8501" || true

echo ""
echo "--- Ollama Instances ---"
check_service "Ollama KGB     :18134" "http://localhost:18134/api/tags" || true
check_service "Ollama GraphQA :18136" "http://localhost:18136/api/tags" || true
check_service "Ollama Ontology:18135" "http://localhost:18135/api/tags" || true

echo ""
echo "--- Ollama Models ---"
check_ollama_models "ollama-kgbuilder " "ollama-kgbuilder" 2>/dev/null || true
check_ollama_models "ollama-graphqa   " "ollama-graphqa" 2>/dev/null || true
check_ollama_models "ollama-ontology  " "ollama-ontology" 2>/dev/null || true

echo ""
echo "=== Done ==="
