"""
Vector Store for RAG System
Manages embeddings and similarity search using HuggingFace models and FAISS
"""

import os
import json
import pickle
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss
from document_processor import Document

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for semantic search using HuggingFace embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", 
                 index_path: str = "./vector_index",
                 force_rebuild: bool = False):
        """
        Initialize vector store
        
        Args:
            model_name: HuggingFace sentence transformer model name
            index_path: Path to save/load vector index
            force_rebuild: Whether to force rebuilding the index
        """
        self.model_name = model_name
        self.index_path = index_path
        self.force_rebuild = force_rebuild
        
        # Initialize embedding model
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
        
        # Initialize FAISS index
        self.index = None
        self.documents: List[Document] = []
        self.document_metadata: List[Dict[str, Any]] = []
        
        # Create index directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
    
    def build_index(self, documents: List[Document]) -> bool:
        """
        Build vector index from documents
        
        Args:
            documents: List of Document objects to index
            
        Returns:
            bool: Success status
        """
        try:
            # Check if index exists and should be loaded
            if not self.force_rebuild and self._index_exists():
                logger.info("Loading existing vector index...")
                return self._load_index()
            
            logger.info(f"Building vector index for {len(documents)} documents...")
            
            # Extract text content for embedding
            texts = [doc.content for doc in documents]
            
            # Generate embeddings in batches
            batch_size = 32
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.embedding_model.encode(
                    batch_texts,
                    show_progress_bar=True,
                    normalize_embeddings=True
                )
                embeddings.extend(batch_embeddings)
                
                if i % 100 == 0:
                    logger.info(f"Processed {i}/{len(texts)} documents")
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Create FAISS index
            self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for normalized vectors
            self.index.add(embeddings_array)
            
            # Store documents and metadata
            self.documents = documents
            self.document_metadata = [
                {
                    'chunk_id': doc.chunk_id,
                    'source': doc.source,
                    'category': doc.category,
                    'metadata': doc.metadata
                }
                for doc in documents
            ]
            
            # Save index to disk
            self._save_index()
            
            logger.info(f"Successfully built vector index with {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error building vector index: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5, 
               category_filter: Optional[str] = None,
               min_score: float = 0.0) -> List[Tuple[Document, float]]:
        """
        Search for similar documents
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            category_filter: Filter results by category
            min_score: Minimum similarity score threshold
            
        Returns:
            List of (Document, similarity_score) tuples
        """
        try:
            if self.index is None:
                logger.error("Vector index not initialized")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                [query],
                normalize_embeddings=True
            )[0]
            
            # Perform similarity search
            scores, indices = self.index.search(
                query_embedding.reshape(1, -1).astype('float32'),
                min(top_k * 2, len(self.documents))  # Get more results for filtering
            )
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= len(self.documents):
                    continue
                    
                doc = self.documents[idx]
                similarity_score = float(score)
                
                # Apply filters
                if min_score > 0 and similarity_score < min_score:
                    continue
                
                if category_filter and doc.category != category_filter:
                    continue
                
                results.append((doc, similarity_score))
                
                if len(results) >= top_k:
                    break
            
            logger.debug(f"Found {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def search_by_categories(self, query: str, categories: List[str], 
                           top_k_per_category: int = 2) -> Dict[str, List[Tuple[Document, float]]]:
        """
        Search for documents across multiple categories
        
        Args:
            query: Search query text
            categories: List of categories to search in
            top_k_per_category: Number of results per category
            
        Returns:
            Dictionary mapping category to list of (Document, score) tuples
        """
        results = {}
        
        for category in categories:
            category_results = self.search(
                query=query,
                top_k=top_k_per_category,
                category_filter=category
            )
            if category_results:
                results[category] = category_results
        
        return results
    
    def get_relevant_context(self, query: str, max_context_length: int = 2000) -> str:
        """
        Get relevant context for a query, formatted as a single string
        
        Args:
            query: Search query
            max_context_length: Maximum length of context to return
            
        Returns:
            Formatted context string
        """
        try:
            # Search for relevant documents
            results = self.search(query, top_k=8)
            
            if not results:
                return ""
            
            context_parts = []
            current_length = 0
            
            for doc, score in results:
                # Format document info
                doc_info = f"[{doc.category.upper()}] {doc.content}"
                
                # Add metadata if available
                if doc.metadata.get('importance'):
                    doc_info += f" (Importance: {doc.metadata['importance']})"
                if doc.metadata.get('timeframe'):
                    doc_info += f" (Timeframe: {doc.metadata['timeframe']})"
                
                # Check if adding this would exceed max length
                if current_length + len(doc_info) > max_context_length:
                    break
                
                context_parts.append(doc_info)
                current_length += len(doc_info)
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ""
    
    def _index_exists(self) -> bool:
        """Check if vector index files exist"""
        index_file = os.path.join(self.index_path, "faiss.index")
        docs_file = os.path.join(self.index_path, "documents.pkl")
        metadata_file = os.path.join(self.index_path, "metadata.json")
        
        return all(os.path.exists(f) for f in [index_file, docs_file, metadata_file])
    
    def _save_index(self):
        """Save vector index and metadata to disk"""
        try:
            # Save FAISS index
            index_file = os.path.join(self.index_path, "faiss.index")
            faiss.write_index(self.index, index_file)
            
            # Save documents
            docs_file = os.path.join(self.index_path, "documents.pkl")
            with open(docs_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            # Save metadata
            metadata_file = os.path.join(self.index_path, "metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(self.document_metadata, f, indent=2)
            
            # Save model info
            model_info = {
                'model_name': self.model_name,
                'embedding_dim': self.embedding_dim,
                'num_documents': len(self.documents)
            }
            
            model_file = os.path.join(self.index_path, "model_info.json")
            with open(model_file, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            logger.info("Vector index saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving vector index: {e}")
            raise
    
    def _load_index(self) -> bool:
        """Load vector index and metadata from disk"""
        try:
            # Load model info and verify compatibility
            model_file = os.path.join(self.index_path, "model_info.json")
            if os.path.exists(model_file):
                with open(model_file, 'r') as f:
                    model_info = json.load(f)
                
                if model_info.get('model_name') != self.model_name:
                    logger.warning(f"Model mismatch: {model_info.get('model_name')} vs {self.model_name}")
                    return False
            
            # Load FAISS index
            index_file = os.path.join(self.index_path, "faiss.index")
            self.index = faiss.read_index(index_file)
            
            # Load documents
            docs_file = os.path.join(self.index_path, "documents.pkl")
            with open(docs_file, 'rb') as f:
                self.documents = pickle.load(f)
            
            # Load metadata
            metadata_file = os.path.join(self.index_path, "metadata.json")
            with open(metadata_file, 'r') as f:
                self.document_metadata = json.load(f)
            
            logger.info(f"Loaded vector index with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error loading vector index: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        if not self.documents:
            return {}
        
        # Count by category
        category_counts = {}
        for doc in self.documents:
            category_counts[doc.category] = category_counts.get(doc.category, 0) + 1
        
        return {
            'total_documents': len(self.documents),
            'embedding_dimension': self.embedding_dim,
            'model_name': self.model_name,
            'categories': category_counts,
            'index_size_mb': self.index.ntotal * self.embedding_dim * 4 / (1024 * 1024) if self.index else 0
        }
    
    def rebuild_index(self, documents: List[Document]) -> bool:
        """Force rebuild the vector index"""
        self.force_rebuild = True
        return self.build_index(documents) 