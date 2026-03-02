#!/usr/bin/env bash
set -euo pipefail

FUSEKI_URL="${FUSEKI_URL:-http://localhost:3030}"
FUSEKI_DATASET="${FUSEKI_DATASET:-kgbuilder}"
FUSEKI_ADMIN_PASSWORD="${FUSEKI_ADMIN_PASSWORD:-admin}"

echo "=== Seed Ontology into Fuseki ==="

# 1. Create dataset if it doesn't exist
echo "[1/2] Creating Fuseki dataset '$FUSEKI_DATASET'..."
curl -s -u "admin:${FUSEKI_ADMIN_PASSWORD}" \
    -X POST "${FUSEKI_URL}/\$/datasets" \
    -d "dbName=${FUSEKI_DATASET}&dbType=tdb2" \
    2>/dev/null || echo "  (dataset may already exist)"

# 2. Upload ontology file(s)
ONTOLOGY_DIR="${ONTOLOGY_DIR:-data/ontology}"

if [[ -d "$ONTOLOGY_DIR" ]]; then
    echo "[2/2] Uploading ontology files from $ONTOLOGY_DIR ..."
    for owl_file in "$ONTOLOGY_DIR"/*.{owl,ttl,rdf} 2>/dev/null; do
        if [[ -f "$owl_file" ]]; then
            echo "  → Uploading $(basename "$owl_file")..."
            content_type="application/rdf+xml"
            [[ "$owl_file" == *.ttl ]] && content_type="text/turtle"
            curl -s -u "admin:${FUSEKI_ADMIN_PASSWORD}" \
                -X POST "${FUSEKI_URL}/${FUSEKI_DATASET}/data" \
                -H "Content-Type: ${content_type}" \
                --data-binary @"$owl_file"
            echo " ✓"
        fi
    done
else
    echo "[2/2] No ontology directory found at $ONTOLOGY_DIR — skipping upload"
fi

echo ""
echo "=== Seed complete ==="
echo "Fuseki SPARQL endpoint: ${FUSEKI_URL}/${FUSEKI_DATASET}/sparql"
