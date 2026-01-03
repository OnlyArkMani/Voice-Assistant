from typing import List, Dict
import os
import PyPDF2
from utils.vector_store import VectorStore
from config import Config

class RetrievalAgent:
    """Retrieves relevant SOP documents using RAG"""
    
    def __init__(self):
        self.vector_store = VectorStore(
            persist_directory=Config.VECTOR_DB_DIR,
            collection_name=Config.COLLECTION_NAME,
            model_name=Config.EMBEDDING_MODEL
        )
        self.sops_loaded = False
    
    def load_sops_from_directory(self, directory: str = None):
        """Load all PDF SOPs from directory into vector store"""
        if directory is None:
            directory = Config.SOPS_DIR
        
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created SOP directory: {directory}")
            return
        
        documents = []
        for filename in os.listdir(directory):
            if filename.endswith('.pdf'):
                filepath = os.path.join(directory, filename)
                text = self._extract_text_from_pdf(filepath)
                
                # Split into chunks for better retrieval
                chunks = self._chunk_text(text, chunk_size=500, overlap=50)
                
                for i, chunk in enumerate(chunks):
                    documents.append({
                        'id': f"{filename}_chunk_{i}",
                        'text': chunk,
                        'metadata': {
                            'source': filename,
                            'chunk_index': i
                        }
                    })
        
        if documents:
            self.vector_store.add_documents(documents)
            self.sops_loaded = True
            print(f"Loaded {len(documents)} chunks from {len(os.listdir(directory))} SOPs")
        else:
            print("No PDF files found in SOP directory")
    
    def _extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text content from PDF"""
        text = ""
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        return text
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """Retrieve relevant SOP sections for a query"""
        if top_k is None:
            top_k = Config.TOP_K_RESULTS
        
        if not self.sops_loaded and self.vector_store.get_collection_count() == 0:
            return [{
                'text': 'No SOPs loaded yet. Please upload SOP documents.',
                'metadata': {'source': 'system'},
                'distance': 0
            }]
        
        results = self.vector_store.search(query, top_k=top_k)
        return results
    
    def get_context_for_query(self, query: str) -> str:
        """Get formatted context string for LLM"""
        results = self.retrieve(query)
        
        context = "Relevant SOP Information:\n\n"
        for i, result in enumerate(results, 1):
            context += f"[Source {i}: {result['metadata']['source']}]\n"
            context += f"{result['text']}\n\n"
        
        return context