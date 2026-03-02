"""Build KG — Trigger and monitor KG construction pipeline."""

import streamlit as st
import httpx
import time

KGBUILDER_API = "http://kgbuilder-api:8001"

st.set_page_config(page_title="Build KG", page_icon="🏗️", layout="wide")
st.title("🏗️ Build Knowledge Graph")

st.markdown("Configure and launch a KG construction pipeline run.")

# --- Build Configuration ---
with st.form("build_config"):
    col1, col2 = st.columns(2)
    with col1:
        ontology_path = st.text_input(
            "Ontology Path",
            value="data/ontology/plan-ontology-v1.0.owl",
        )
        document_dir = st.text_input(
            "Document Directory",
            value="data/documents",
        )
        model = st.text_input("LLM Model", value="qwen3:8b")
    with col2:
        max_iterations = st.slider("Max Iterations", 1, 50, 5)
        questions_per_class = st.slider("Questions per Class", 1, 20, 3)
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.5)

    submitted = st.form_submit_button("🚀 Start Build", type="primary")

if submitted:
    try:
        resp = httpx.post(
            f"{KGBUILDER_API}/api/v1/build",
            json={
                "ontology_path": ontology_path,
                "document_dir": document_dir,
                "max_iterations": max_iterations,
                "questions_per_class": questions_per_class,
                "confidence_threshold": confidence_threshold,
                "model": model,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        st.success(f"Build started! Job ID: `{data['job_id']}`")
        st.session_state["current_job_id"] = data["job_id"]
    except Exception as e:
        st.error(f"Failed to start build: {e}")

# --- Job Status ---
st.divider()
st.subheader("Job Status")

job_id = st.text_input(
    "Job ID",
    value=st.session_state.get("current_job_id", ""),
    placeholder="Enter a job ID to check status",
)

if job_id:
    try:
        resp = httpx.get(f"{KGBUILDER_API}/api/v1/build/{job_id}", timeout=5)
        resp.raise_for_status()
        status = resp.json()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Status", status["status"])
        col2.metric("Progress", f"{status['progress']:.0%}")
        col3.metric("Entities", status["entities_count"])
        col4.metric("Relations", status["relations_count"])

        if status.get("error"):
            st.error(f"Error: {status['error']}")

        st.progress(status["progress"])
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            st.warning("Job not found")
        else:
            st.error(f"Error: {e}")
    except Exception as e:
        st.error(f"Cannot reach KGBuilder API: {e}")

# --- Validation ---
st.divider()
st.subheader("Validation")

if st.button("🔍 Run Validation"):
    try:
        resp = httpx.post(
            f"{KGBUILDER_API}/api/v1/validate",
            json={"run_shacl": True, "run_rules": True, "run_consistency": True},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        if result["passed"]:
            st.success(f"✅ All {result['total_checks']} checks passed ({result['pass_rate']:.0%})")
        else:
            st.warning(f"⚠️ {result['total_checks']} checks — {result['pass_rate']:.0%} pass rate")
            for v in result["violations"]:
                st.json(v)
    except Exception as e:
        st.error(f"Validation error: {e}")
