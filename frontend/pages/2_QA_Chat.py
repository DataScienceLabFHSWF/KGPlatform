"""QA Chat — Ask questions against the knowledge graph."""

import json

import streamlit as st
import httpx

GRAPHQA_API = "http://graphqa-api:8002"

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
    strategy = st.selectbox("Strategy", ["auto", "cypher", "vector", "hybrid"])
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
                # SSE streaming
                placeholder = st.empty()
                full_response = ""

                with httpx.Client(timeout=60) as client:
                    with client.stream(
                        "POST",
                        f"{GRAPHQA_API}/api/v1/chat",
                        json={
                            "session_id": st.session_state.chat_session_id,
                            "message": prompt,
                            "strategy": strategy,
                            "language": language,
                            "stream": True,
                        },
                    ) as response:
                        for line in response.iter_lines():
                            if line.startswith("data: "):
                                data = json.loads(line[6:])
                                if data.get("done"):
                                    break
                                full_response += data.get("token", "")
                                placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": full_response,
                })
            else:
                # Non-streaming
                resp = httpx.post(
                    f"{GRAPHQA_API}/api/v1/chat",
                    json={
                        "session_id": st.session_state.chat_session_id,
                        "message": prompt,
                        "strategy": strategy,
                        "language": language,
                        "stream": False,
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()

                st.session_state.chat_session_id = data.get("session_id")
                answer = data.get("answer", "")
                st.markdown(answer)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": answer,
                })

                # Show metadata
                with st.expander("Details"):
                    st.metric("Confidence", f"{data.get('confidence', 0):.2f}")
                    if data.get("reasoning_chain"):
                        st.write("**Reasoning Chain:**")
                        for step in data["reasoning_chain"]:
                            st.write(f"- {step}")
                    if data.get("provenance"):
                        st.write("**Provenance:**")
                        st.json(data["provenance"])

        except Exception as e:
            st.error(f"Error: {e}")
