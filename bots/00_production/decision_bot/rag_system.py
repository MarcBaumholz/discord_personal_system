"""
RAG System for Decision Bot
Main component that coordinates document processing, embedding, and retrieval
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from document_processor import DocumentProcessor, Document
from vector_store import VectorStore

logger = logging.getLogger(__name__)

class RAGSystem:
    """Main RAG system for intelligent document retrieval"""
    
    def __init__(self, upload_folder: str = "./upload", 
                 model_name: str = "all-MiniLM-L6-v2",
                 index_path: str = "./vector_index",
                 force_rebuild: bool = False):
        """
        Initialize RAG system
        
        Args:
            upload_folder: Path to folder containing documents
            model_name: HuggingFace model for embeddings
            index_path: Path for vector index storage
            force_rebuild: Whether to force rebuild the index
        """
        self.upload_folder = upload_folder
        self.model_name = model_name
        self.index_path = index_path
        self.force_rebuild = force_rebuild
        
        # Initialize components
        self.doc_processor = DocumentProcessor(upload_folder)
        self.vector_store = VectorStore(model_name, index_path, force_rebuild)
        
        # Track initialization status
        self.is_initialized = False
        self.documents = []
        
        # Category mappings for better retrieval
        self.category_keywords = {
            'health_fitness': ['health', 'fitness', 'exercise', 'nutrition', 'sleep', 'wellness', 'body'],
            'career': ['work', 'job', 'career', 'professional', 'skills', 'productivity', 'business'],
            'character': ['personality', 'values', 'integrity', 'authenticity', 'character', 'beliefs'],
            'emotional': ['feelings', 'emotions', 'happiness', 'stress', 'mental', 'mood'],
            'spirituality': ['meditation', 'mindfulness', 'purpose', 'meaning', 'spiritual', 'energy'],
            'social_life': ['friends', 'social', 'relationships', 'communication', 'network'],
            'finance': ['money', 'financial', 'budget', 'investment', 'wealth', 'income'],
            'quality_of_life': ['travel', 'adventure', 'leisure', 'hobbies', 'fun', 'lifestyle'],
            'house_environment': ['home', 'house', 'environment', 'living', 'space'],
            'intellectual': ['learning', 'education', 'knowledge', 'thinking', 'creativity'],
            'family': ['family', 'parenting', 'children', 'marriage', 'partner'],
            'values': ['principles', 'beliefs', 'morals', 'ethics', 'important'],
            'goals': ['objectives', 'targets', 'ambitions', 'plans', 'future']
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the RAG system by processing documents and building index
        
        Returns:
            bool: Success status
        """
        try:
            logger.info("Initializing RAG system...")
            
            # Process all documents
            self.documents = self.doc_processor.process_all_documents()
            
            if not self.documents:
                logger.warning("No documents found to process")
                return False
            
            # Build vector index
            success = self.vector_store.build_index(self.documents)
            
            if success:
                self.is_initialized = True
                logger.info(f"RAG system initialized with {len(self.documents)} documents")
                
                # Log statistics
                stats = self.get_system_stats()
                logger.info(f"Document categories: {list(stats['doc_categories'].keys())}")
                
                return True
            else:
                logger.error("Failed to build vector index")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing RAG system: {e}")
            return False
    
    def get_relevant_context(self, question: str, max_context_length: int = 2000) -> str:
        """
        Get relevant context for a decision question
        
        Args:
            question: The decision question
            max_context_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        if not self.is_initialized:
            logger.warning("RAG system not initialized")
            return ""
        
        try:
            # Determine relevant categories based on question content
            relevant_categories = self._identify_relevant_categories(question)
            
            if relevant_categories:
                # Search within relevant categories
                category_results = self.vector_store.search_by_categories(
                    question, relevant_categories, top_k_per_category=2
                )
                
                # Also do a general search
                general_results = self.vector_store.search(question, top_k=3)
                
                # Combine and format results
                context = self._format_context_from_results(
                    category_results, general_results, max_context_length
                )
            else:
                # Fall back to general search
                context = self.vector_store.get_relevant_context(question, max_context_length)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ""
    
    def search_personal_data(self, query: str, category: Optional[str] = None, 
                           top_k: int = 5) -> List[Tuple[Document, float]]:
        """
        Search personal data with optional category filtering
        
        Args:
            query: Search query
            category: Optional category filter
            top_k: Number of results to return
            
        Returns:
            List of (Document, similarity_score) tuples
        """
        if not self.is_initialized:
            return []
        
        return self.vector_store.search(
            query=query,
            top_k=top_k,
            category_filter=category
        )
    
    def get_values_context(self, question: str) -> str:
        """Get context specifically from personal values"""
        values_results = self.search_personal_data(question, category='values', top_k=3)
        
        if not values_results:
            return ""
        
        context_parts = []
        for doc, score in values_results:
            context_parts.append(f"Personal Value: {doc.content}")
        
        return "\n".join(context_parts)
    
    def get_goals_context(self, question: str) -> str:
        """Get context specifically from personal goals"""
        goals_results = self.search_personal_data(question, category='goals', top_k=3)
        
        if not goals_results:
            return ""
        
        context_parts = []
        for doc, score in goals_results:
            context_parts.append(f"Personal Goal: {doc.content}")
        
        return "\n".join(context_parts)
    
    def get_life_area_context(self, question: str, life_area: str) -> str:
        """Get context from a specific life area"""
        area_results = self.search_personal_data(question, category=life_area, top_k=2)
        
        if not area_results:
            return ""
        
        context_parts = []
        for doc, score in area_results:
            context_parts.append(f"[{life_area.upper()}] {doc.content}")
        
        return "\n".join(context_parts)
    
    def _identify_relevant_categories(self, question: str) -> List[str]:
        """
        Identify relevant categories based on question content
        
        Args:
            question: The decision question
            
        Returns:
            List of relevant category names
        """
        question_lower = question.lower()
        relevant_categories = []
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in question_lower:
                    relevant_categories.append(category)
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_categories = []
        for cat in relevant_categories:
            if cat not in seen:
                seen.add(cat)
                unique_categories.append(cat)
        
        return unique_categories[:4]  # Limit to top 4 categories
    
    def _format_context_from_results(self, category_results: Dict[str, List[Tuple[Document, float]]], 
                                   general_results: List[Tuple[Document, float]], 
                                   max_length: int) -> str:
        """
        Format context from search results
        
        Args:
            category_results: Results by category
            general_results: General search results
            max_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        used_chunks = set()
        
        # Add category-specific results first
        for category, results in category_results.items():
            for doc, score in results:
                if doc.chunk_id in used_chunks:
                    continue
                
                doc_text = f"[{category.upper()}] {doc.content}"
                
                if current_length + len(doc_text) > max_length:
                    break
                
                context_parts.append(doc_text)
                current_length += len(doc_text)
                used_chunks.add(doc.chunk_id)
        
        # Add general results if we have space
        for doc, score in general_results:
            if doc.chunk_id in used_chunks:
                continue
            
            if current_length + len(doc.content) > max_length:
                break
            
            context_parts.append(f"[{doc.category.upper()}] {doc.content}")
            current_length += len(doc.content)
            used_chunks.add(doc.chunk_id)
        
        return "\n\n".join(context_parts)
    
    async def reload_data(self) -> bool:
        """Reload and reindex all data"""
        try:
            logger.info("Reloading RAG system data...")
            
            # Set force rebuild
            self.vector_store.force_rebuild = True
            
            # Reinitialize
            return await self.initialize()
            
        except Exception as e:
            logger.error(f"Error reloading RAG data: {e}")
            return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            'is_initialized': self.is_initialized,
            'total_documents': len(self.documents),
            'doc_categories': {},
            'vector_store_stats': {}
        }
        
        if self.documents:
            # Document statistics
            doc_stats = self.doc_processor.get_document_stats()
            stats['doc_categories'] = doc_stats.get('categories', {})
            stats['total_words'] = doc_stats.get('total_words', 0)
            
            # Vector store statistics
            if self.is_initialized:
                vector_stats = self.vector_store.get_index_stats()
                stats['vector_store_stats'] = vector_stats
        
        return stats
    
    def get_status_report(self) -> str:
        """Get a formatted status report"""
        stats = self.get_system_stats()
        
        if not stats['is_initialized']:
            return "RAG System: ❌ Not initialized"
        
        report_lines = [
            "🧠 RAG System Status: ✅ Initialized",
            f"📄 Documents: {stats['total_documents']}",
            f"📊 Categories: {', '.join(stats['doc_categories'].keys())}",
            f"🔍 Vector Model: {self.model_name}"
        ]
        
        if 'vector_store_stats' in stats:
            vs_stats = stats['vector_store_stats']
            report_lines.append(f"💾 Index Size: {vs_stats.get('index_size_mb', 0):.1f} MB")
        
        return "\n".join(report_lines) 