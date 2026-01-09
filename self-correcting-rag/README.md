# Self-Correcting RAG for AI Governance & Compliance

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](app.py)

## 🎯 What it does
Multi-agent RAG pipeline that answers questions about AI regulation, ethics, and compliance with **built-in fact-checking** to prevent hallucination.

**Key innovation**: Relevance filtering + self-fact-checking with confidence scores before answering.

## 📊 Demo


## 🛠️ Architecture
User Query → Retrieval → Relevance Agent → Generator → Fact-Check → Decision Logic



## 🚀 Quickstart
```bash
pip install -r requirements.txt
python download_ai_documents.py  # Downloads 32 governance PDFs
streamlit run app.py