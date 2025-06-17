import logging
from typing import List, Optional
import os
from pathlib import Path
from langchain.schema import Document as LangchainDocument
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class VectorStore:
    """Handles document storage and retrieval using FAISS vector store."""
    
    def __init__(self, persist_directory: str = "vector_store"):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory to persist the vector store
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize or load vector store
        self.store = self._load_or_create_store()
    
    def _load_or_create_store(self) -> FAISS:
        """Load existing vector store or create a new one."""
        try:
            if (self.persist_directory / "index.faiss").exists():
                logger.info("Loading existing vector store")
                return FAISS.load_local(
                    self.persist_directory,
                    self.embeddings
                )
            else:
                logger.info("Creating new vector store")
                return FAISS.from_texts(
                    ["Initial document"],
                    self.embeddings
                )
        except Exception as e:
            logger.error(f"Error loading/creating vector store: {e}")
            raise
    
    def add_documents(self, documents: List[LangchainDocument]) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.store.add_documents(documents)
            self.store.save_local(self.persist_directory)
            return True
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def similarity_search(self, query: str, k: int = 4) -> List[LangchainDocument]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        try:
            return self.store.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []
    
    def clear(self) -> bool:
        """
        Clear the vector store.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a new empty store
            self.store = FAISS.from_texts(
                ["Initial document"],
                self.embeddings
            )
            self.store.save_local(self.persist_directory)
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False 