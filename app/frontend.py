import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Enterprise AI Knowledge Assistant", page_icon="📚", layout="wide")
st.title("📚 Enterprise AI Knowledge Assistant")
st.caption("Upload enterprise PDFs and ask questions grounded in your documents.")

with st.sidebar:
    st.header("1. Upload documents")
    uploaded = st.file_uploader("Choose a PDF", type=["pdf"])
    if st.button("Upload and index", disabled=uploaded is None, use_container_width=True):
        with st.spinner("Extracting, chunking and indexing your PDF..."):
            try:
                response = requests.post(
                    f"{API_URL}/upload-pdf",
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                    timeout=180,
                )
                response.raise_for_status()
                st.success("Document indexed successfully")
                st.json(response.json())
            except requests.RequestException as exc:
                st.error(f"Upload failed: {exc}")

    st.divider()
    st.caption("Backend status")
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        st.success("API healthy" if health.ok else "API unavailable")
    except requests.RequestException:
        st.error("API unavailable")

st.header("2. Ask a question")
question = st.text_area("Enter a question about your uploaded documents", height=100,
                        placeholder="Example: What is the annual leave policy?")
top_k = st.slider("Number of relevant passages", min_value=1, max_value=10, value=4)

if st.button("Ask assistant", type="primary", use_container_width=True):
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        with st.spinner("Searching documents and generating an answer..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question, "top_k": top_k},
                    timeout=300,
                )
                response.raise_for_status()
                result = response.json()
                st.subheader("Answer")
                st.write(result["answer"])
                st.subheader("Sources")
                for source in result.get("sources", []):
                    st.write(f"- {source}")
            except requests.HTTPError as exc:
                try:
                    st.error(exc.response.json().get("detail", str(exc)))
                except Exception:
                    st.error(str(exc))
            except requests.RequestException as exc:
                st.error(f"Could not contact the API: {exc}")
