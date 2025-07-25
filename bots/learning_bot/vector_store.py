import logging
from typing import List, Optional
import os
from pathlib import Path
from langchain.schema import Document as LangchainDocument
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np
import random

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
        
        # Use HuggingFaceEmbeddings for better compatibility
        logger.info("Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize or load vector store
        self.store = self._load_or_create_store()
    
    def _load_or_create_store(self) -> FAISS:
        """Load existing vector store or create a new one."""
        try:
            if (self.persist_directory / "index.faiss").exists():
                logger.info("Loading existing vector store")
                return FAISS.load_local(
                    str(self.persist_directory),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                logger.info("Creating new vector store")
                return FAISS.from_texts(
                    ["Initial document"],
                    self.embeddings
                )
        except Exception as e:
            logger.error(f"Error loading/creating vector store: {e}")
            # Create a new store if loading fails
            return FAISS.from_texts(
                ["Initial document"],
                self.embeddings
            )
    
    def add_documents(self, documents: List[LangchainDocument]) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if documents:
                self.store.add_documents(documents)
                self.store.save_local(str(self.persist_directory))
                logger.info(f"Added {len(documents)} documents to vector store")
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
            results = self.store.similarity_search(query, k=k)
            # Filter out the initial document
            filtered_results = [doc for doc in results if doc.page_content != "Initial document"]
            return filtered_results
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []
    
    def get_random_documents(self, k: int = 3) -> List[LangchainDocument]:
        """
        Get random documents from the vector store.
        
        Args:
            k: Number of random documents to return
            
        Returns:
            List of random documents
        """
        try:
            # Get many documents with a broad search
            all_docs = self.store.similarity_search("learning knowledge book", k=50)
            if not all_docs:
                # Try alternative search terms
                all_docs = self.store.similarity_search("", k=50)
            
            # Filter out the initial document
            filtered_docs = [doc for doc in all_docs if doc.page_content != "Initial document"]
            
            if not filtered_docs:
                logger.warning("No documents found in vector store")
                return []
            
            # Return random selection
            selected_docs = random.sample(filtered_docs, min(k, len(filtered_docs)))
            logger.info(f"Selected {len(selected_docs)} random documents from {len(filtered_docs)} available")
            return selected_docs
        except Exception as e:
            logger.error(f"Error getting random documents: {e}")
            return []
    
    def get_document_count(self) -> int:
        """Get the total number of documents in the store."""
        try:
            # Use similarity search to get an estimate
            docs = self.store.similarity_search("", k=100)
            filtered_docs = [doc for doc in docs if doc.page_content != "Initial document"]
            return len(filtered_docs)
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
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
            self.store.save_local(str(self.persist_directory))
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False 