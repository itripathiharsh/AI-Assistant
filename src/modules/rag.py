import os
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configuration for data paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
CHROMA_DB_PATH = os.path.join(BASE_DIR, 'data', 'chroma_db')

class RAGSystem:
    def __init__(self):
        print("Initializing RAG System...")
        self.embeddings = self._initialize_embeddings()
        if self.embeddings is None:
            raise RuntimeError("Failed to load embedding model. RAG System cannot proceed.")
        self.vector_store = self._initialize_vector_store()
        if self.vector_store is None:
            raise RuntimeError("Failed to initialize vector store. RAG System cannot proceed.")
        print("RAG System initialized.")

    def _initialize_embeddings(self):
        """Initializes the HuggingFace embedding model."""
        print("Loading embedding model (sentence-transformers/bge-small-en-v1.5)...")
        try:
            model_name = "BAAI/bge-small-en-v1.5"
            model_kwargs = {'device': 'cpu'}
            encode_kwargs = {'normalize_embeddings': True}
            embeddings = HuggingFaceBgeEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            print("Embedding model loaded successfully.")
            return embeddings
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            print("Please ensure `sentence-transformers` is installed and you have an internet connection for model download.")
            return None

    def _initialize_vector_store(self):
        """Initializes or loads the Chroma vector store."""
        if os.path.exists(CHROMA_DB_PATH) and os.listdir(CHROMA_DB_PATH):
            print(f"Loading existing ChromaDB from {CHROMA_DB_PATH}...")
            # When loading existing, the argument is 'embedding_function'
            vector_store = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=self.embeddings)
            print("ChromaDB loaded.")
        else:
            print(f"Creating new ChromaDB at {CHROMA_DB_PATH}...")
            os.makedirs(CHROMA_DB_PATH, exist_ok=True)
            docs = self._load_and_process_knowledge_base()
            if not docs:
                print("No documents to add to ChromaDB. Please check your knowledge base data.")
                return None
            
            
            vector_store = Chroma.from_documents(
                documents=docs, 
                embedding=self.embeddings, 
                persist_directory=CHROMA_DB_PATH
            )
            
            
            vector_store.persist()
            print("ChromaDB created and persisted.")
        return vector_store

    def _load_and_process_knowledge_base(self):
        """Loads and processes the structured knowledge base into LangChain Documents."""
        knowledge_base_path = os.path.join(PROCESSED_DATA_DIR, 'knowledge_base.json')
        if not os.path.exists(knowledge_base_path):
            print(f"Knowledge base JSON not found at {knowledge_base_path}.")
            return []

        with open(knowledge_base_path, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)

        documents = []
        
        if "scenario_based_rebuttals" in kb_data:
            for item in kb_data["scenario_based_rebuttals"]:
                scenario = item.get("scenario", "")
                rebuttals = item.get("rebuttals", [])
                content = f"Scenario: {scenario}\nRebuttals: " + "\n".join(rebuttals)
                documents.append(Document(page_content=content, metadata={"source": "knowledge_base", "type": "rebuttal", "scenario": scenario}))

        for key, value in kb_data.items():
            if key not in ["scenario_based_rebuttals"]:
                content = f"{key.replace('_', ' ').title()}: {json.dumps(value, indent=2)}"
                documents.append(Document(page_content=content, metadata={"source": "knowledge_base", "type": key}))
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        split_docs = text_splitter.split_documents(documents)
        print(f"Processed {len(documents)} raw documents into {len(split_docs)} chunks.")
        return split_docs

    def retrieve_documents(self, query, k=3):
        """
        Retrieves top-k relevant documents for a given query from the vector store.
        """
        if not self.vector_store:
            print("Vector store not initialized. Cannot retrieve documents.")
            return []
        
        print(f"Retrieving documents for query: '{query[:50]}...'")
        retrieved_docs = self.vector_store.similarity_search(query, k=k)
        print(f"Retrieved {len(retrieved_docs)} documents.")
        return retrieved_docs

# Basic test of the RAG system
if __name__ == "__main__":
    print("🔧 Testing RAGSystem...")
    try:
        rag_system = RAGSystem()

        if rag_system.vector_store:
            query_1 = "I don't want to pay premiums anymore, it was sold as single premium."
            docs_1 = rag_system.retrieve_documents(query_1)
            print("\n--- Retrieved Documents for Query 1 ---")
            for i, doc in enumerate(docs_1):
                print(f"Document {i+1} (Source: {doc.metadata.get('source')} | Type: {doc.metadata.get('type')}):")
                print(doc.page_content[:200], "...")
                print("-" * 20)

            query_2 = "What are the effective returns and charges on my policy?"
            docs_2 = rag_system.retrieve_documents(query_2)
            print("\n--- Retrieved Documents for Query 2 ---")
            for i, doc in enumerate(docs_2):
                print(f"Document {i+1} (Source: {doc.metadata.get('source')} | Type: {doc.metadata.get('type')}):")
                print(doc.page_content[:200], "...")
                print("-" * 20)
        else:
            print("RAG System failed to initialize. Check previous error messages.")
    except RuntimeError as e:
        print(f"Fatal RAG System initialization error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during RAG test: {e}")