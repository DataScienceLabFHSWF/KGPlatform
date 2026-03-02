"""QA Chat — Ask questions against the knowledge graph."""

import json

import os

import streamlit as st
import httpx

GRAPHQA_API = os.environ.get("GRAPHQA_API_URL", "http://graphqa-api:8002")

st.set_page_config(page_title="QA Chat", page_icon="💬", layout="wide")
st.title("💬 QA Chat")

st.markdown("Ask questions about the knowledge graph using natural language.")

# --- Session management ---
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# --- Sidebar settings ---
with st.sidebar:
    st.subheader("Settings")
    strategy = st.selectbox(
        "Strategy",
        ["hybrid_sota", "hybrid", "agentic", "cypher", "vector_only", "graph_only"],
        format_func=lambda s: {
            "hybrid_sota": "Hybrid SOTA (Ontology-Informed)",
            "hybrid": "Hybrid Fusion (RRF)",
            "agentic": "Agentic ReAct",
            "cypher": "Cypher Query Generation",
            "vector_only": "Vector Search",
            "graph_only": "Graph Traversal",
        }.get(s, s),
    )
    language = st.selectbox("Language", ["de", "en"])
    streaming = st.checkbox("Streaming", value=True)

    if st.button("🔄 New Session"):
        st.session_state.chat_session_id = None
        st.session_state.chat_messages = []
        st.rerun()

# --- Chat display ---
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User input ---
if prompt := st.chat_input("Ask a question about the knowledge graph..."):
    # Display user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send to API
    with st.chat_message("assistant"):
        try:
            if streaming:
                # SSE streaming — API sends named events:
                #   event: session       → {"session_id": "..."}
                #   event: reasoning_step → {"step": N, "text": "..."}
                #   event: token         → {"text": "..."}
                #   event: evidence      → [...]
                #   event: provenance    → [...]
                #   event: subgraph      → {"nodes":[], "edges":[]}
                #   event: done          → {"confidence": ..., "latency_ms": ...}
                placeholder = st.empty()
                full_response = ""
                reasoning_steps = []
                metadata = {}
                current_event = None

                with httpx.Client(timeout=httpx.Timeout(10, read=180)) as client:
                    with client.stream(
                        "POST",
                        f"{GRAPHQA_API}/api/v1/chat/send",
                        json={
                            "session_id": st.session_state.chat_session_id,
                            "message": prompt,
                            "strategy": strategy,
                            "language": language,
                            "stream": True,
                        },
                    ) as response:
                        for line in response.iter_lines():
                            line = line.strip()
                            if not line:
                                current_event = None
                                continue
                            if line.startswith("event: "):
                                current_event = line[7:]
                                continue
                            if line.startswith("data: "):
                                payload = line[6:]
                                try:
                                    data = json.loads(payload)
                                except json.JSONDecodeError:
                                    continue

                                if current_event == "session":
                                    st.session_state.chat_session_id = data.get("session_id")
                                elif current_event == "token":
                                    full_response += data.get("text", "")
                                    placeholder.markdown(full_response + "▌")
                                elif current_event == "reasoning_step":
                                    reasoning_steps.append(data.get("text", ""))
                                elif current_event == "done":
                                    metadata = data
                                # evidence/provenance/subgraph captured in metadata

                placeholder.markdown(full_response)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": full_response,
                })

                # Show metadata
                with st.expander("Details"):
                    if metadata.get("confidence") is not None:
                        st.metric("Confidence", f"{metadata['confidence']:.2f}")
                    if metadata.get("latency_ms"):
                        st.caption(f"Latency: {metadata['latency_ms']:.0f} ms · Strategy: {metadata.get('strategy', strategy)}")
                    if reasoning_steps:
                        st.write("**Reasoning Chain:**")
                        for step in reasoning_steps:
                            st.write(f"- {step}")
            else:
                # Non-streaming
                resp = httpx.post(
                    f"{GRAPHQA_API}/api/v1/chat/send",
                    json={
                        "session_id": st.session_state.chat_session_id,
                        "message": prompt,
                        "strategy": strategy,
                        "language": language,
                        "stream": False,
                    },
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()

                st.session_state.chat_session_id = data.get("session_id")
                answer = data.get("message", {}).get("content", "")
                st.markdown(answer)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": answer,
                })

                # Show metadata
                with st.expander("Details"):
                    st.metric("Confidence", f"{data.get('confidence', 0):.2f}")
                    if data.get("latency_ms"):
                        st.caption(f"Latency: {data['latency_ms']:.0f} ms · Strategy: {data.get('strategy_used', strategy)}")
                    if data.get("reasoning_chain"):
                        st.write("**Reasoning Chain:**")
                        for step in data["reasoning_chain"]:
                            st.write(f"- {step}")
                    if data.get("provenance"):
                        st.write("**Provenance:**")
                        st.json(data["provenance"])

        except Exception as e:
            st.error(f"Error: {e}")
