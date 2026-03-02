"""Review — HITL expert review workflow."""

import os

import streamlit as st
import httpx

KGBUILDER_API = os.environ.get("KGBUILDER_API_URL", "http://kgbuilder-api:8001")
GRAPHQA_API = os.environ.get("GRAPHQA_API_URL", "http://graphqa-api:8002")

st.set_page_config(page_title="Review", page_icon="📋", layout="wide")
st.title("📋 HITL Review Workflow")

st.markdown("""
Expert review interface for the Human-in-the-Loop feedback loop:
1. **Gap Detection** — View gaps detected from QA results
2. **Feedback Submission** — Accept, reject, or modify proposed changes
3. **Low-Confidence Reports** — Report QA issues back to KGBuilder
""")

# --- Gap Report ---
st.subheader("Gap Report")

if st.button("🔍 Fetch Latest Gaps"):
    try:
        resp = httpx.get(f"{KGBUILDER_API}/api/v1/hitl/gaps", timeout=10)
        resp.raise_for_status()
        gaps = resp.json()

        col1, col2 = st.columns(2)
        col1.metric("Coverage Score", f"{gaps['coverage_score']:.2f}")
        col2.metric("Untyped Entities", len(gaps["untyped_entities"]))

        if gaps["untyped_entities"]:
            st.write("**Untyped Entities:**")
            for entity in gaps["untyped_entities"]:
                st.write(f"  - {entity}")

        if gaps["failed_queries"]:
            st.write("**Failed Queries:**")
            for query in gaps["failed_queries"]:
                st.write(f"  - {query}")

        if gaps["suggested_new_classes"]:
            st.write("**Suggested New Classes:**")
            for cls in gaps["suggested_new_classes"]:
                st.write(f"  - {cls}")

        if gaps["suggested_new_relations"]:
            st.write("**Suggested New Relations:**")
            for rel in gaps["suggested_new_relations"]:
                st.write(f"  - {rel}")

        if gaps["low_confidence_answers"]:
            st.write("**Low Confidence Answers:**")
            for answer in gaps["low_confidence_answers"]:
                st.json(answer)

        if not any([
            gaps["untyped_entities"],
            gaps["failed_queries"],
            gaps["suggested_new_classes"],
            gaps["suggested_new_relations"],
            gaps["low_confidence_answers"],
        ]):
            st.success("No gaps detected!")

    except Exception as e:
        st.error(f"Cannot fetch gaps: {e}")

# --- Feedback Submission ---
st.divider()
st.subheader("Submit Expert Feedback")

with st.form("feedback_form"):
    review_item_id = st.text_input("Review Item ID")
    reviewer_id = st.text_input("Reviewer ID")
    decision = st.selectbox(
        "Decision",
        ["accepted", "rejected", "modified", "needs_discussion"],
    )
    rationale = st.text_area("Rationale")
    confidence = st.slider("Confidence", 0.0, 1.0, 1.0)
    new_cqs = st.text_area(
        "New Competency Questions (one per line)",
        placeholder="Enter new CQs to test...",
    )

    submitted = st.form_submit_button("📤 Submit Feedback", type="primary")

if submitted and review_item_id and reviewer_id:
    cq_list = [q.strip() for q in new_cqs.split("\n") if q.strip()] if new_cqs else []
    try:
        resp = httpx.post(
            f"{KGBUILDER_API}/api/v1/hitl/feedback",
            json={
                "review_item_id": review_item_id,
                "reviewer_id": reviewer_id,
                "decision": decision,
                "rationale": rationale,
                "confidence": confidence,
                "new_competency_questions": cq_list,
            },
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        st.success(f"Feedback submitted: {result['status']} → Routed to: {', '.join(result['routed_to'])}")
    except Exception as e:
        st.error(f"Feedback error: {e}")

# --- Low Confidence Reporting ---
st.divider()
st.subheader("Report Low-Confidence QA Results")

st.markdown("Manually trigger gap detection from recent low-confidence QA answers.")

if st.button("🔄 Trigger Gap Detection from QA"):
    try:
        # Fetch from GraphQA HITL endpoint
        resp = httpx.post(
            f"{GRAPHQA_API}/api/v1/hitl/report-low-confidence",
            json={"qa_results": []},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        st.info(
            f"Status: {result['status']} | "
            f"Gaps detected: {result['gaps_detected']} | "
            f"Suggested classes: {', '.join(result['suggested_classes']) or 'none'}"
        )
    except Exception as e:
        st.error(f"Error: {e}")
