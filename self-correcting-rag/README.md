# Self-Correcting RAG for AI Governance & Compliance

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](app.py)

## 🎯 What it does
Multi-agent RAG pipeline that answers questions about AI regulation, ethics, and compliance with **built-in fact-checking** to prevent hallucination.

**Key innovation**: Relevance filtering + self-fact-checking with confidence scores before answering.

## 📊 Demo


## 🛠️ Architecture
User Query → Retrieval → Relevance Agent → Generator → Fact-Check → Decision Logic

  🤖 Self-Correcting RAG Pipeline
                    ┌──────────────────────────────────────┐
User Question ─────→│ 1. RETRIEVAL (ChromaDB Vector Search) │
                    │                                        │
                    ↓                                        │
                    │ 2. RELEVANCE AGENT                     │
                    │   • LLM scores each doc (1-10)         │───❌ Filtered
                    │   • Only 6+/10 docs pass → Generator   │
                    ↓                                        │
                    │ 3. GENERATOR AGENT                     │
                    │   • Writes answer from filtered docs   │
                    ↓                                        │
                    │ 4. FACT-CHECK AGENT                    │
                    │   • Scores answer 0-100% consistency   │───🔄 Retry if <90%
                    │   • Flags unsupported claims           │
                    └───────────┬──────────────────────────────┘
                                ↓
                          Answer + Confidence Score

## 🚀 Quickstart
```bash
pip install -r requirements.txt
python download_ai_documents.py  # Downloads 32 governance PDFs
streamlit run app.py

🛠️ Tech Stack
Component	Technology	Why?
Retrieval	ChromaDB + all-MiniLM-L6-v2	Local vector DB, CPU-friendly
LLM	Groq llama3.3-70b-versatile	Fastest inference (300+ t/s), free tier
Framework	LangChain	Industry standard RAG tooling
Frontend	Streamlit	Production UI in 50 lines
Deployment	Streamlit Cloud	Free, auto-scales
