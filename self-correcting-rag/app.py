import streamlit as st
import os
import glob
from main import SelfCorrectingRAG

st.set_page_config(page_title="Self-Correcting AI Governance RAG", layout="wide")
st.title("🤖 Self-Correcting RAG for AI Governance & Compliance")

st.markdown("""
Ask questions about AI regulation, ethics, risk management, and compliance.  
**Live demo** of multi-agent RAG with self-fact-checking.
""")

@st.cache_resource
def download_governance_docs():
    """Download key AI governance PDFs on first run."""
    st.info("📥 Downloading governance documents (runs once)...")
    
    # Sample high-quality PDFs (subset for speed)
    urls = {
        "EU_AI_Act_Summary.pdf": "https://artificialintelligenceact.eu/wp-content/uploads/2024/08/AI-Act-HIGH-LEVEL-SUMMARY.pdf",
        "NIST_AI_RMF.pdf": "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf",
        "EU_AI_Ethics_Guidelines.pdf": "https://ec.europa.eu/info/sites/default/files/ethics-guidelines-trustworthy-ai.pdf",
    }
    
    os.makedirs("data", exist_ok=True)
    for filename, url in urls.items():
        filepath = f"data/{filename}"
        if not os.path.exists(filepath):
            import requests
            resp = requests.get(url)
            with open(filepath, "wb") as f:
                f.write(resp.content)
            st.success(f"Downloaded {filename}")
    
    return [f"data/{f}" for f in os.listdir("data") if f.endswith(".pdf")]

@st.cache_resource
def load_rag():
    pdf_paths = download_governance_docs()
    rag = SelfCorrectingRAG()
    num_chunks = rag.load_documents(pdf_paths)
    st.success(f"✅ Loaded {num_chunks} chunks from {len(pdf_paths)} PDFs")
    return rag

rag = load_rag()

col1, col2 = st.columns([4, 1])
with col1:
    question = st.text_input(
        "Your question:",
        placeholder="What are prohibited AI practices under EU AI Act?",
    )
with col2:
    max_retries = st.slider("Max retries", 0, 2, 1)

if st.button("🔍 Ask", type="primary") and question:
    with st.spinner("Running self-correcting pipeline..."):
        result = rag.query(question, max_retries=max_retries)

    st.subheader("📝 Answer")
    st.write(result["answer"])

    st.subheader("📊 Quality Metrics")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Confidence", f"{result['confidence']}%")
    with col_b:
        st.metric("Status", result["status"])
    with col_c:
        st.metric("Sources used", result["num_sources"])

    details = result.get("fact_check_details", {})
    with st.expander("🔍 Fact-check details"):
        st.json(details)

    unsupported = details.get("unsupported_claims", [])
    if unsupported:
        st.warning(f"⚠️ {len(unsupported)} unsupported claims flagged")

st.caption("🛠️ LangChain + ChromaDB + Groq + AI governance PDFs | Deployed on Streamlit Cloud")
