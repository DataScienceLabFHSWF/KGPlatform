"""KGPlatform — unified frontend."""

import streamlit as st

st.set_page_config(
    page_title="KGPlatform",
    page_icon="🔗",
    layout="wide",
)

st.title("KGPlatform")
st.markdown("""
Unified interface for the Knowledge Graph research ecosystem:
- **Build KG** — Trigger and monitor KG construction
- **QA Chat** — Ask questions against the knowledge graph
- **Ontology** — Browse and extend the ontology
- **Review** — HITL expert review workflow
""")

# Health check all services
import os
import httpx

KGBUILDER_API = os.environ.get("KGBUILDER_API_URL", "http://kgbuilder-api:8001")
GRAPHQA_API = os.environ.get("GRAPHQA_API_URL", "http://graphqa-api:8002")
ONTOLOGY_API = os.environ.get("ONTOLOGY_API_URL", "http://ontology-api:8010")

services = {
    "KGBuilder": f"{KGBUILDER_API}/api/v1/health",
    "GraphQA": f"{GRAPHQA_API}/api/v1/health",
    "Ontology": f"{ONTOLOGY_API}/api/v1/health",
}

cols = st.columns(len(services))
for col, (name, url) in zip(cols, services.items()):
    try:
        r = httpx.get(url, timeout=3)
        col.metric(name, "✅ Online")
    except Exception:
        col.metric(name, "❌ Offline")
