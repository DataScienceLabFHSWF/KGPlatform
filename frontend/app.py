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
import httpx

services = {
    "KGBuilder": "http://kgbuilder-api:8001/api/v1/health",
    "GraphQA": "http://graphqa-api:8002/api/v1/health",
    "Ontology": "http://ontology-api:8003/api/v1/health",
}

cols = st.columns(len(services))
for col, (name, url) in zip(cols, services.items()):
    try:
        r = httpx.get(url, timeout=3)
        col.metric(name, "✅ Online")
    except Exception:
        col.metric(name, "❌ Offline")
