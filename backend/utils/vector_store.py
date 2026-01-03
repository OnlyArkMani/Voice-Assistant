import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import os

class VectorStore:
    """Handles vector embeddings and similarity search for SOP documents"""
    
    def __init__(self, persist_directory: str, collection_name: str, model_name: str):
        # Initialize ChromaDB with persistence
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Load embedding model (runs locally, no API needed)
        self.embedding_model = SentenceTransformer(model_name)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to vector store
        documents: [{"id": "doc1", "text": "content", "metadata": {...}}]
        """
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        print(f"Added {len(documents)} documents to vector store")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar documents"""
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return formatted_results
    
    def get_collection_count(self) -> int:
        """Get number of documents in collection"""
        return self.collection.count()