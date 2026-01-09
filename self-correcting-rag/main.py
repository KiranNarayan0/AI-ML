import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List, Dict
import json

# Load environment variables
load_dotenv()

class SelfCorrectingRAG:
    def __init__(self):
        print("🚀 Initializing Self-Correcting RAG System...")
        
        # Initialize Groq LLM - Fast and Free!
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=1000,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Initialize embeddings (runs on CPU)
        print("📦 Loading embedding model (this may take a minute first time)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        self.vectorstore = None
        print("✅ Initialization complete!")
        
    def load_documents(self, directory: str = "./data"):
        """Load and process documents from directory"""
        print(f"\n📚 Loading documents from {directory}...")
        
        # Load all text and PDF files from directory
        documents = []
        
        # Load text files
        if os.path.exists(directory):
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if file.endswith('.txt'):
                    loader = TextLoader(file_path)
                    documents.extend(loader.load())
                    print(f"   Loaded: {file}")
                elif file.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                    documents.extend(loader.load())
                    print(f"   Loaded: {file}")
        
        if not documents:
            print("⚠️  No documents found! Please add .txt or .pdf files to the data/ directory")
            return 0
        
        # Split documents into chunks
        print("✂️  Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # Create vector store
        print("🔢 Creating vector embeddings...")
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
        
        print(f"✅ Loaded and indexed {len(splits)} document chunks from {len(documents)} documents")
        return len(splits)
    
    def retrieve_documents(self, query: str, k: int = 5):
        """Step 1: Retrieve relevant documents"""
        print(f"\n{'='*70}")
        print(f"🔍 STEP 1: RETRIEVAL")
        print(f"{'='*70}")
        print(f"Query: '{query}'")
        
        if not self.vectorstore:
            print("❌ Error: No documents loaded! Please run load_documents() first.")
            return []
        
        docs = self.vectorstore.similarity_search(query, k=k)
        print(f"✅ Retrieved {len(docs)} potentially relevant documents")
        return docs
    
    def relevance_agent(self, query: str, documents: List) -> List:
        """Step 2: Filter documents for relevance"""
        print(f"\n{'='*70}")
        print(f"🎯 STEP 2: RELEVANCE FILTERING")
        print(f"{'='*70}")
        
        relevant_docs = []
        
        for i, doc in enumerate(documents):
            # Truncate document for relevance check to save tokens
            doc_preview = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
            
            prompt = f"""You are a document relevance evaluator for AI compliance, ethics, and governance queries.

USER QUESTION: {query}

DOCUMENT EXCERPT:
{doc_preview}

TASK: Rate how relevant this document is for answering the user's question.
Consider: Does it contain information that directly addresses the question?

Respond ONLY with valid JSON (no markdown):
{{"relevance_score": <1-10>, "reason": "<brief explanation>"}}"""
            
            try:
                response = self.llm.invoke(prompt)
                result = json.loads(response.content.strip())
                score = result.get('relevance_score', 0)
                reason = result.get('reason', 'No reason provided')
                
                if score >= 7:
                    relevant_docs.append(doc)
                    print(f"✅ Document {i+1}: Score {score}/10 - KEPT")
                    print(f"   Reason: {reason}")
                else:
                    print(f"❌ Document {i+1}: Score {score}/10 - FILTERED")
                    print(f"   Reason: {reason}")
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  Document {i+1}: JSON parsing error - keeping by default")
                relevant_docs.append(doc)
            except Exception as e:
                print(f"⚠️  Document {i+1}: Error ({str(e)}) - keeping by default")
                relevant_docs.append(doc)
        
        print(f"\n📊 Result: {len(relevant_docs)}/{len(documents)} documents passed relevance filter")
        return relevant_docs
    
    def generator_agent(self, query: str, relevant_docs: List) -> str:
        """Step 3: Generate answer from relevant documents"""
        print(f"\n{'='*70}")
        print(f"✍️  STEP 3: ANSWER GENERATION")
        print(f"{'='*70}")
        
        # Combine relevant documents into context
        context = "\n\n".join([
            f"[Source {i+1}]\n{doc.page_content}" 
            for i, doc in enumerate(relevant_docs)
        ])
        
        prompt = f"""You are an expert AI compliance and ethics consultant.

REFERENCE DOCUMENTS:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer using ONLY information from the reference documents above
2. Cite sources by referencing [Source 1], [Source 2], etc.
3. If information is insufficient, explicitly state what's missing
4. Be precise and specific - this is for compliance purposes
5. Structure your answer clearly

ANSWER:"""
        
        response = self.llm.invoke(prompt)
        answer = response.content
        
        print(f"✅ Generated answer ({len(answer)} characters)")
        print(f"Preview: {answer[:150]}...")
        
        return answer
    
    def fact_check_agent(self, query: str, answer: str, relevant_docs: List) -> Dict:
        """Step 4: Fact-check the generated answer"""
        print(f"\n{'='*70}")
        print(f"🔍 STEP 4: FACT-CHECKING")
        print(f"{'='*70}")
        
        context = "\n\n".join([
            f"[Source {i+1}]\n{doc.page_content}" 
            for i, doc in enumerate(relevant_docs)
        ])
        
        prompt = f"""You are a fact-checking expert specializing in AI compliance and ethics content.

SOURCE DOCUMENTS:
{context}

GENERATED ANSWER:
{answer}

ORIGINAL QUESTION: {query}

TASK: Verify factual consistency between the answer and source documents.

Instructions:
1. Identify key factual claims in the answer
2. Check if each claim is supported by the source documents
3. Note any claims that are unsupported or potentially hallucinated
4. Assign an overall consistency score (0-100%)

Respond ONLY with valid JSON (no markdown):
{{
  "consistency_score": <0-100>,
  "supported_claims": ["claim1", "claim2"],
  "unsupported_claims": ["claim1"],
  "verdict": "<brief overall assessment>"
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            result = json.loads(response.content.strip())
            
            score = result.get('consistency_score', 70)
            supported = result.get('supported_claims', [])
            unsupported = result.get('unsupported_claims', [])
            verdict = result.get('verdict', 'Assessment completed')
            
            print(f"📊 Consistency Score: {score}%")
            print(f"✅ Supported claims: {len(supported)}")
            print(f"❌ Unsupported claims: {len(unsupported)}")
            print(f"💭 Verdict: {verdict}")
            
            if unsupported:
                print(f"\n⚠️  ISSUES DETECTED:")
                for claim in unsupported:
                    print(f"   - {claim}")
            
            return {
                "consistency_score": score,
                "supported_claims": supported,
                "unsupported_claims": unsupported,
                "verdict": verdict
            }
            
        except Exception as e:
            print(f"⚠️  Fact-check parsing error: {e}")
            print("   Defaulting to medium confidence (70%)")
            return {
                "consistency_score": 70,
                "supported_claims": [],
                "unsupported_claims": [],
                "verdict": "Unable to fully verify - proceed with caution"
            }
    
    def query(self, question: str, max_retries: int = 1) -> Dict:
        """Complete self-correcting RAG pipeline with retry logic"""
        print(f"\n{'#'*70}")
        print(f"🤖 SELF-CORRECTING RAG PIPELINE")
        print(f"{'#'*70}")
        print(f"Question: {question}\n")
        
        attempt = 0
        best_result = None
        
        while attempt <= max_retries:
            if attempt > 0:
                print(f"\n🔄 Retry attempt {attempt}/{max_retries}...")
            
            # Step 1: Retrieve
            documents = self.retrieve_documents(question)
            
            if not documents:
                return {
                    "answer": "No documents found in the knowledge base.",
                    "confidence": 0,
                    "status": "NO_DOCUMENTS",
                    "fact_check_details": {},
                    "num_sources": 0
                }
            
            # Step 2: Filter relevance
            relevant_docs = self.relevance_agent(question, documents)
            
            if not relevant_docs:
                return {
                    "answer": "I couldn't find relevant information to answer this question in the available documents.",
                    "confidence": 0,
                    "status": "NO_RELEVANT_DOCS",
                    "fact_check_details": {},
                    "num_sources": 0
                }
            
            # Step 3: Generate answer
            answer = self.generator_agent(question, relevant_docs)
            
            # Step 4: Fact-check
            fact_check = self.fact_check_agent(question, answer, relevant_docs)
            
            score = fact_check['consistency_score']
            
            result = {
                "answer": answer,
                "confidence": score,
                "fact_check_details": fact_check,
                "num_sources": len(relevant_docs)
            }
            
            # Determine status and decide if retry needed
            if score >= 90:
                result["status"] = "HIGH_CONFIDENCE"
                best_result = result
                break  # Good enough, no retry needed
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
        
        # Final decision
        print(f"\n{'='*70}")
        print(f"📋 FINAL DECISION")
        print(f"{'='*70}")
        
        final_score = best_result['confidence']
        status = best_result['status']
        
        if final_score >= 90:
            print(f"✅ HIGH CONFIDENCE ({final_score}%)")
            print(f"   → Answer approved for delivery")
        elif final_score >= 70:
            print(f"⚠️  MEDIUM CONFIDENCE ({final_score}%)")
            print(f"   → Answer delivered with caution notice")
        else:
            print(f"❌ LOW CONFIDENCE ({final_score}%)")
            print(f"   → Answer quality below threshold")
        
        print(f"📚 Used {best_result['num_sources']} source document(s)")
        
        return best_result


# Test/Demo Script
if __name__ == "__main__":
    print("="*70)
    print("SELF-CORRECTING RAG SYSTEM - DEMO")
    print("="*70)
    
    # Initialize
    rag = SelfCorrectingRAG()
    
    # Create sample compliance document if data folder is empty
    if not os.path.exists("./data"):
        os.makedirs("./data")
    
    sample_doc_path = "./data/sample_ai_act.txt"
    if not os.path.exists(sample_doc_path):
        print("\n📝 Creating sample AI compliance document...")
        sample_content = """
        EU AI Act - Key Provisions
        
        The European Union Artificial Intelligence Act establishes a comprehensive regulatory framework
        for AI systems based on risk levels. The Act categorizes AI systems into four risk categories:
        
        1. UNACCEPTABLE RISK (Prohibited):
        - Social scoring systems by governments
        - Real-time biometric identification in public spaces (with limited exceptions for law enforcement)
        - AI systems that manipulate human behavior to circumvent free will
        - AI systems that exploit vulnerabilities of specific groups
        
        2. HIGH-RISK AI SYSTEMS:
        High-risk AI systems must comply with strict requirements including:
        - Risk management systems
        - High-quality training data and data governance
        - Technical documentation and record-keeping
        - Transparency and provision of information to users
        - Human oversight measures
        - Robustness, accuracy, and cybersecurity
        
        Examples of high-risk AI include:
        - Biometric identification and categorization
        - Critical infrastructure management
        - Educational and vocational training systems
        - Employment, worker management, and self-employment access
        - Access to essential services (credit scoring, emergency services)
        - Law enforcement systems
        - Migration, asylum, and border control management
        - Administration of justice and democratic processes
        
        3. LIMITED RISK:
        Systems with transparency obligations, such as chatbots where users should be
        informed they're interacting with AI.
        
        4. MINIMAL RISK:
        Most AI systems fall here with no specific obligations beyond existing laws.
        
        COMPLIANCE REQUIREMENTS:
        - Providers of high-risk AI must conduct conformity assessments
        - CE marking required for compliant high-risk AI systems
        - Post-market monitoring and incident reporting obligations
        - AI systems must maintain logs for auditing purposes
        
        GOVERNANCE:
        - EU AI Office established for coordination
        - National competent authorities in each member state
        - European Artificial Intelligence Board for guidance
        
        PENALTIES:
        - Up to €35 million or 7% of global annual turnover for prohibited AI violations
        - Up to €15 million or 3% of turnover for other violations
        - Up to €7.5 million or 1.5% of turnover for supplying incorrect information
        
        The Act applies to providers placing AI systems on the EU market and users of AI systems
        within the EU, regardless of where the provider is located.
        """
        
        with open(sample_doc_path, "w") as f:
            f.write(sample_content)
        print(f"✅ Created sample document at {sample_doc_path}")
    
    # Load documents
    num_chunks = rag.load_documents()
    
    if num_chunks == 0:
        print("\n❌ No documents loaded. Please add compliance documents to the ./data directory")
        exit(1)
    
    # Run test query
    print("\n" + "="*70)
    print("RUNNING TEST QUERY")
    print("="*70)
    
    test_question = "What AI practices are prohibited under the EU AI Act?"
    result = rag.query(test_question)
    
    # Display results
    print("\n" + "="*70)
    print("FINAL OUTPUT")
    print("="*70)
    print(f"\n📝 ANSWER:\n{result['answer']}")
    print(f"\n📊 CONFIDENCE: {result['confidence']}%")
    print(f"🏷️  STATUS: {result['status']}")
    print(f"📚 SOURCES USED: {result['num_sources']}")
    
    if result['fact_check_details'].get('unsupported_claims'):
        print(f"\n⚠️  UNSUPPORTED CLAIMS:")
        for claim in result['fact_check_details']['unsupported_claims']:
            print(f"   - {claim}")
    
    print("\n" + "="*70)
    print("✅ Demo complete! System is working.")
    print("="*70)
    