import streamlit as st

from main import SelfCorrectingRAG, get_all_governance_pdfs

st.set_page_config(page_title="Self-Correcting AI Governance RAG", layout="wide")
st.title("🤖 Self-Correcting RAG for AI Governance & Compliance")

st.markdown("""
Ask questions about AI regulation, ethics, risk management, and compliance.  
The system will:
- Retrieve relevant documents from a 32‑PDF governance corpus  
- Filter for relevance using LLM judgment  
- Generate an answer  
- **Fact‑check itself** before responding  
""")

# Load pipeline
@st.cache_resource
def load_rag():
    rag = SelfCorrectingRAG()
    pdf_paths = get_all_governance_pdfs()
    num_chunks = rag.load_documents(pdf_paths)
    st.success(f"✅ Loaded {num_chunks} chunks from {len(pdf_paths)} governance PDFs")
    return rag

rag = load_rag()

col1, col2 = st.columns([4, 1])
with col1:
    question = st.text_input(
        "Your question:",
        placeholder="e.g., What obligations do high-risk AI providers have under EU AI Act?",
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

    st.subheader("🔍 Fact-check details")
    details = result["fact_check_details"]
    st.json(details)

    unsupported = details.get("unsupported_claims", [])
    if unsupported:
        st.warning(f"⚠️ {len(unsupported)} unsupported claims flagged above")

st.caption("Built with LangChain, ChromaDB, Groq LLM, and 32 AI governance PDFs")
