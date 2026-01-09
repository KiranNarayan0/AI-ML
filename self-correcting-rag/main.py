import os
import glob
import json
from typing import List, Dict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load environment variables (for GROQ_API_KEY)
load_dotenv()


def get_all_governance_pdfs(base_folder: str = "AI_Governance_Documents") -> List[str]:
    """
    Return a list of all PDF file paths under the AI governance corpus.
    This expects download_ai_documents.py to have been run already.
    """
    pattern = os.path.join(base_folder, "**", "*.pdf")
    pdfs = glob.glob(pattern, recursive=True)
    return pdfs


class SelfCorrectingRAG:
    def __init__(self):
        print("🚀 Initializing Self-Correcting RAG System...")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment (.env).")

        # Initialize Groq LLM
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=1000,
            api_key=api_key,
        )

        # Initialize embeddings (CPU)
        print("📦 Loading embedding model (all-MiniLM-L6-v2)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )

        self.vectorstore = None
        print("✅ Initialization complete!")

    def load_documents(self, file_paths: List[str]) -> int:
        """Load and index documents from given file paths."""
        print("\n📚 Loading documents...")
        if not file_paths:
            print("⚠️ No file paths provided to load_documents().")
            return 0

        documents = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"⚠️ Skipping missing file: {file_path}")
                continue

            if file_path.lower().endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            else:
                loader = TextLoader(file_path)

            try:
                docs = loader.load()
                documents.extend(docs)
                print(f"   Loaded: {file_path}")
            except Exception as e:
                print(f"   ⚠️ Error loading {file_path}: {e}")

        if not documents:
            print("❌ No documents successfully loaded.")
            return 0

        print("✂️ Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        splits = text_splitter.split_documents(documents)

        print("🔢 Creating vector embeddings and Chroma index...")
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory="./chroma_db",
        )

        print(f"✅ Indexed {len(splits)} chunks from {len(documents)} documents.")
        return len(splits)

    def retrieve_documents(self, query: str, k: int = 5):
        """Step 1: Retrieve relevant documents."""
        print("\n" + "=" * 70)
        print("🔍 STEP 1: RETRIEVAL")
        print("=" * 70)
        print(f"Query: '{query}'")

        if not self.vectorstore:
            print("❌ Error: Vector store is not initialized. Call load_documents() first.")
            return []

        docs = self.vectorstore.similarity_search(query, k=k)
        print(f"✅ Retrieved {len(docs)} potentially relevant documents.")
        return docs

    def relevance_agent(self, query: str, documents: List) -> List:
        """Step 2: Filter documents for relevance."""
        print("\n" + "=" * 70)
        print("🎯 STEP 2: RELEVANCE FILTERING")
        print("=" * 70)

        relevant_docs = []
        for i, doc in enumerate(documents):
            preview = doc.page_content[:500]
            if len(doc.page_content) > 500:
                preview += "..."

            prompt = f"""
You are a document relevance evaluator for AI compliance, ethics, and governance queries.

USER QUESTION:
{query}

DOCUMENT EXCERPT:
{preview}

TASK:
Rate how relevant this document is for answering the question.

Respond ONLY with valid JSON (no markdown), like:
{{"relevance_score": 1-10, "reason": "..."}}
"""

            try:
                response = self.llm.invoke(prompt)
                result = json.loads(response.content.strip())
                score = result.get("relevance_score", 0)
                reason = result.get("reason", "No reason provided")

                if score >= 7:
                    relevant_docs.append(doc)
                    print(f"✅ Doc {i+1}: {score}/10 - KEPT")
                    print(f"   Reason: {reason}")
                else:
                    print(f"❌ Doc {i+1}: {score}/10 - FILTERED")
                    print(f"   Reason: {reason}")
            except Exception as e:
                print(f"⚠️ Doc {i+1}: Error/parsing issue ({e}) - keeping by default.")
                relevant_docs.append(doc)

        print(f"\n📊 Result: {len(relevant_docs)}/{len(documents)} docs passed relevance filter.")
        return relevant_docs

    def generator_agent(self, query: str, relevant_docs: List) -> str:
        """Step 3: Generate answer from relevant documents."""
        print("\n" + "=" * 70)
        print("✍️ STEP 3: ANSWER GENERATION")
        print("=" * 70)

        context = "\n\n".join(
            [f"[Source {i+1}]\n{doc.page_content}" for i, doc in enumerate(relevant_docs)]
        )

        prompt = f"""
You are an expert AI compliance and ethics consultant.

REFERENCE DOCUMENTS:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Answer using ONLY information from the reference documents above.
2. Cite sources as [Source 1], [Source 2], etc.
3. If the documents do not contain enough info, say explicitly what is missing.
4. Be precise and structured. This is for compliance use-cases.
5. Focus on accuracy over creativity.

ANSWER:
"""

        response = self.llm.invoke(prompt)
        answer = response.content
        print(f"✅ Generated answer ({len(answer)} characters).")
        print(f"Preview: {answer[:180]}...")
        return answer

    def fact_check_agent(self, query: str, answer: str, relevant_docs: List) -> Dict:
        """Step 4: Fact-check the generated answer."""
        print("\n" + "=" * 70)
        print("🔍 STEP 4: FACT-CHECKING")
        print("=" * 70)

        context = "\n\n".join(
            [f"[Source {i+1}]\n{doc.page_content}" for i, doc in enumerate(relevant_docs)]
        )

        prompt = f"""
You are a fact-checking expert specializing in AI compliance and ethics.

SOURCE DOCUMENTS:
{context}

GENERATED ANSWER:
{answer}

ORIGINAL QUESTION:
{query}

TASK:
1. Extract key factual claims from the answer.
2. Check whether each claim is supported by the source documents.
3. Identify any unsupported or hallucinated claims.
4. Assign an overall factual consistency score (0-100%).

Respond ONLY with valid JSON (no markdown), like:
{{
  "consistency_score": 0-100,
  "supported_claims": ["..."],
  "unsupported_claims": ["..."],
  "verdict": "..."
}}
"""

        try:
            response = self.llm.invoke(prompt)
            result = json.loads(response.content.strip())
            score = result.get("consistency_score", 70)
            supported = result.get("supported_claims", [])
            unsupported = result.get("unsupported_claims", [])
            verdict = result.get("verdict", "Assessment completed")

            print(f"📊 Consistency Score: {score}%")
            print(f"✅ Supported claims: {len(supported)}")
            print(f"❌ Unsupported claims: {len(unsupported)}")
            print(f"💭 Verdict: {verdict}")

            if unsupported:
                print("\n⚠️ Unsupported / problematic claims:")
                for claim in unsupported:
                    print(f" - {claim}")

            return {
                "consistency_score": score,
                "supported_claims": supported,
                "unsupported_claims": unsupported,
                "verdict": verdict,
            }
        except Exception as e:
            print(f"⚠️ Fact-check parsing error: {e}")
            print("   Defaulting to medium confidence (70%).")
            return {
                "consistency_score": 70,
                "supported_claims": [],
                "unsupported_claims": [],
                "verdict": "Unable to fully verify - proceed with caution",
            }

    def query(self, question: str, max_retries: int = 1) -> Dict:
        """Full self-correcting RAG pipeline with optional retry."""
        print("\n" + "#" * 70)
        print("🤖 SELF-CORRECTING RAG PIPELINE")
        print("#" * 70)
        print(f"Question: {question}\n")

        attempt = 0
        best_result = None

        while attempt <= max_retries:
            if attempt > 0:
                print(f"\n🔄 Retry attempt {attempt}/{max_retries}...\n")

            docs = self.retrieve_documents(question)
            if not docs:
                return {
                    "answer": "No documents found in the knowledge base.",
                    "confidence": 0,
                    "status": "NO_DOCUMENTS",
                    "fact_check_details": {},
                    "num_sources": 0,
                }

            relevant_docs = self.relevance_agent(question, docs)
            if not relevant_docs:
                return {
                    "answer": "I could not find relevant information for this question in the documents.",
                    "confidence": 0,
                    "status": "NO_RELEVANT_DOCS",
                    "fact_check_details": {},
                    "num_sources": 0,
                }

            answer = self.generator_agent(question, relevant_docs)
            fact_check = self.fact_check_agent(question, answer, relevant_docs)
            score = fact_check["consistency_score"]

            result = {
                "answer": answer,
                "confidence": score,
                "fact_check_details": fact_check,
                "num_sources": len(relevant_docs),
            }

            if score >= 90:
                result["status"] = "HIGH_CONFIDENCE"
                best_result = result
                break
            elif score >= 70:
                result["status"] = "MEDIUM_CONFIDENCE"
                if not best_result or score > best_result["confidence"]:
                    best_result = result
                attempt += 1
            else:
                result["status"] = "LOW_CONFIDENCE"
                if not best_result or score > best_result["confidence"]:
                    best_result = result
                attempt += 1

        # Final decision logging
        print("\n" + "=" * 70)
        print("📋 FINAL DECISION")
        print("=" * 70)

        final_score = best_result["confidence"]
        status = best_result["status"]

        if final_score >= 90:
            print(f"✅ HIGH CONFIDENCE ({final_score}%) → Answer approved")
        elif final_score >= 70:
            print(f"⚠️ MEDIUM CONFIDENCE ({final_score}%) → Answer with caution")
        else:
            print(f"❌ LOW CONFIDENCE ({final_score}%) → Below threshold")

        print(f"📚 Sources used: {best_result['num_sources']}")
        return best_result


if __name__ == "__main__":
    print("=" * 70)
    print("SELF-CORRECTING RAG SYSTEM - GOVERNANCE CORPUS DEMO")
    print("=" * 70)

    rag = SelfCorrectingRAG()

    pdf_paths = get_all_governance_pdfs()
    print(f"\n📂 Found {len(pdf_paths)} PDF files in AI_Governance_Documents/")

    if not pdf_paths:
        print("❌ No PDFs found. Run: python download_ai_documents.py")
        raise SystemExit(1)

    num_chunks = rag.load_documents(pdf_paths)
    if num_chunks == 0:
        print("❌ No chunks were indexed. Check your documents.")
        raise SystemExit(1)

    test_question = "What AI practices are prohibited or considered unacceptable risk under the EU AI Act?"
    print("\n" + "=" * 70)
    print("RUNNING TEST QUERY")
    print("=" * 70)

    result = rag.query(test_question)

    print("\n" + "=" * 70)
    print("FINAL OUTPUT")
    print("=" * 70)
    print("\n📝 ANSWER:\n")
    print(result["answer"])
    print(f"\n📊 CONFIDENCE: {result['confidence']}%")
    print(f"🏷️ STATUS: {result['status']}")
    print(f"📚 SOURCES USED: {result['num_sources']}")

    unsupported = result["fact_check_details"].get("unsupported_claims") or []
    if unsupported:
        print("\n⚠️ UNSUPPORTED CLAIMS:")
        for claim in unsupported:
            print(f" - {claim}")

    print("\n" + "=" * 70)
    print("✅ Demo complete.")
    print("=" * 70)
