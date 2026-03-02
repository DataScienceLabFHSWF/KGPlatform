"""Ontology — Browse and extend the ontology."""

import streamlit as st
import httpx

ONTOLOGY_API = "http://ontology-api:8003"

st.set_page_config(page_title="Ontology", page_icon="🧬", layout="wide")
st.title("🧬 Ontology Browser")

st.markdown("Browse the current ontology structure and apply extensions.")

# --- Summary ---
st.subheader("Ontology Summary")

try:
    resp = httpx.get(f"{ONTOLOGY_API}/api/v1/ontology/summary", timeout=10)
    resp.raise_for_status()
    summary = resp.json()

    col1, col2 = st.columns(2)
    col1.metric("Classes", summary["class_count"])
    col2.metric("Relations", summary["relation_count"])

    # --- Classes ---
    st.subheader("Classes")
    if summary["classes"]:
        for cls in summary["classes"]:
            with st.expander(f"📦 {cls['label']} ({cls['uri']})"):
                st.write(f"**Description:** {cls['description']}")
                if cls.get("parent_uri"):
                    st.write(f"**Parent:** {cls['parent_uri']}")
                if cls.get("properties"):
                    st.write("**Properties:**")
                    for prop in cls["properties"]:
                        st.write(f"  - {prop}")
                if cls.get("examples"):
                    st.write(f"**Examples:** {', '.join(cls['examples'])}")
    else:
        st.info("No classes loaded yet. Seed an ontology first.")

    # --- Relations ---
    st.subheader("Relations")
    if summary["relations"]:
        for rel in summary["relations"]:
            with st.expander(f"🔗 {rel['label']} ({rel['uri']})"):
                st.write(f"**Description:** {rel['description']}")
                st.write(f"**Domain:** {', '.join(rel['domain'])}")
                st.write(f"**Range:** {', '.join(rel['range'])}")
    else:
        st.info("No relations loaded yet.")

except Exception as e:
    st.error(f"Cannot reach Ontology API: {e}")

# --- SHACL Validation ---
st.divider()
st.subheader("SHACL Validation")

if st.button("🔍 Run SHACL Validation"):
    try:
        resp = httpx.post(
            f"{ONTOLOGY_API}/api/v1/validate/shacl",
            json={},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        if result["conforms"]:
            st.success(f"✅ Graph conforms ({result['total_shapes']} shapes checked)")
        else:
            st.warning(f"⚠️ {len(result['violations'])} violation(s)")
            for v in result["violations"]:
                st.json(v)
    except Exception as e:
        st.error(f"Validation error: {e}")

# --- Manual Extension ---
st.divider()
st.subheader("Extend Ontology")

with st.form("extend_form"):
    change_type = st.selectbox(
        "Change Type",
        ["tbox_new_class", "tbox_modify_class", "tbox_hierarchy_fix", "tbox_property_fix"],
    )
    review_item_id = st.text_input("Review Item ID")
    reviewer_id = st.text_input("Reviewer ID")
    rationale = st.text_area("Rationale")
    confidence = st.slider("Confidence", 0.0, 1.0, 1.0)

    submitted = st.form_submit_button("📤 Submit Extension", type="primary")

if submitted and review_item_id and reviewer_id:
    try:
        resp = httpx.post(
            f"{ONTOLOGY_API}/api/v1/extend",
            json={
                "change_type": change_type,
                "review_item_id": review_item_id,
                "reviewer_id": reviewer_id,
                "rationale": rationale,
                "confidence": confidence,
            },
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        st.success(f"Extension submitted: {result['status']} (ID: {result['change_id']})")
    except Exception as e:
        st.error(f"Extension error: {e}")
