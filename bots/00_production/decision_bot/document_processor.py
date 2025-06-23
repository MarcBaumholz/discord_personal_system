"""
Document Processor for RAG System
Processes CSV and Markdown files for embedding and retrieval
"""

import os
import re
import pandas as pd
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Represents a processed document chunk"""
    content: str
    metadata: Dict[str, Any]
    source: str
    category: str
    chunk_id: str

class DocumentProcessor:
    """Processes various document types for RAG system"""
    
    def __init__(self, upload_folder: str = "./upload"):
        self.upload_folder = upload_folder
        self.documents: List[Document] = []
        
    def process_all_documents(self) -> List[Document]:
        """Process all documents in the upload folder"""
        self.documents = []
        
        try:
            # Process CSV files
            csv_docs = self._process_csv_files()
            self.documents.extend(csv_docs)
            
            # Process Markdown files
            md_docs = self._process_markdown_files()
            self.documents.extend(md_docs)
            
            logger.info(f"Processed {len(self.documents)} document chunks")
            return self.documents
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            return []
    
    def _process_csv_files(self) -> List[Document]:
        """Process CSV files into document chunks"""
        documents = []
        
        for filename in os.listdir(self.upload_folder):
            if filename.endswith('.csv'):
                file_path = os.path.join(self.upload_folder, filename)
                
                try:
                    df = pd.read_csv(file_path)
                    
                    # Determine category based on filename and content
                    category = self._determine_csv_category(filename, df)
                    
                    # Process each row as a document
                    for idx, row in df.iterrows():
                        content = self._format_csv_row_content(row, category)
                        
                        doc = Document(
                            content=content,
                            metadata={
                                'source_file': filename,
                                'row_index': idx,
                                'importance': self._extract_importance(row),
                                'timeframe': self._extract_timeframe(row),
                                'priority': self._extract_priority(row)
                            },
                            source=filename,
                            category=category,
                            chunk_id=f"{filename}_{idx}"
                        )
                        documents.append(doc)
                        
                    logger.info(f"Processed {filename}: {len(df)} rows")
                    
                except Exception as e:
                    logger.error(f"Error processing CSV {filename}: {e}")
        
        return documents
    
    def _process_markdown_files(self) -> List[Document]:
        """Process Markdown files into document chunks"""
        documents = []
        
        for filename in os.listdir(self.upload_folder):
            if filename.endswith('.md'):
                file_path = os.path.join(self.upload_folder, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split content into meaningful chunks
                    chunks = self._split_markdown_content(content, filename)
                    documents.extend(chunks)
                    
                    logger.info(f"Processed {filename}: {len(chunks)} chunks")
                    
                except Exception as e:
                    logger.error(f"Error processing Markdown {filename}: {e}")
        
        return documents
    
    def _split_markdown_content(self, content: str, filename: str) -> List[Document]:
        """Split markdown content into semantic chunks"""
        documents = []
        
        # Split by major sections (## headers)
        sections = re.split(r'\n## ', content)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Extract section title and content
            lines = section.split('\n')
            if i == 0:  # First section might not have ##
                title = lines[0] if lines else "Introduction"
            else:
                title = lines[0] if lines else f"Section {i}"
            
            # Determine category from section title or filename
            category = self._determine_markdown_category(title, filename)
            
            # Split long sections into smaller chunks
            section_chunks = self._split_large_section(section, title, category)
            
            for j, chunk_content in enumerate(section_chunks):
                if len(chunk_content.strip()) < 50:  # Skip very short chunks
                    continue
                    
                doc = Document(
                    content=chunk_content,
                    metadata={
                        'source_file': filename,
                        'section_title': title,
                        'section_index': i,
                        'chunk_index': j,
                        'word_count': len(chunk_content.split())
                    },
                    source=filename,
                    category=category,
                    chunk_id=f"{filename}_{i}_{j}"
                )
                documents.append(doc)
        
        return documents
    
    def _split_large_section(self, section: str, title: str, category: str, max_chunk_size: int = 800) -> List[str]:
        """Split large sections into smaller chunks"""
        if len(section) <= max_chunk_size:
            return [section]
        
        chunks = []
        
        # Try to split by subsections first (### headers)
        subsections = re.split(r'\n### ', section)
        
        current_chunk = ""
        
        for subsection in subsections:
            if len(current_chunk + subsection) <= max_chunk_size:
                current_chunk += subsection + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = subsection + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If chunks are still too large, split by paragraphs
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= max_chunk_size:
                final_chunks.append(chunk)
            else:
                # Split by paragraphs
                paragraphs = chunk.split('\n\n')
                current_para_chunk = ""
                
                for para in paragraphs:
                    if len(current_para_chunk + para) <= max_chunk_size:
                        current_para_chunk += para + "\n\n"
                    else:
                        if current_para_chunk:
                            final_chunks.append(current_para_chunk.strip())
                        current_para_chunk = para + "\n\n"
                
                if current_para_chunk:
                    final_chunks.append(current_para_chunk.strip())
        
        return final_chunks if final_chunks else [section]
    
    def _determine_csv_category(self, filename: str, df: pd.DataFrame) -> str:
        """Determine category from CSV filename and content"""
        filename_lower = filename.lower()
        
        if 'value' in filename_lower or 'wert' in filename_lower:
            return 'values'
        elif 'goal' in filename_lower or 'ziel' in filename_lower:
            return 'goals'
        elif 'experience' in filename_lower or 'learning' in filename_lower:
            return 'experiences'
        elif 'identity' in filename_lower or 'personality' in filename_lower:
            return 'identity'
        
        # Check column names for hints
        columns = [col.lower() for col in df.columns]
        if any(word in ' '.join(columns) for word in ['value', 'wert', 'principle']):
            return 'values'
        elif any(word in ' '.join(columns) for word in ['goal', 'ziel', 'objective']):
            return 'goals'
        
        return 'general'
    
    def _determine_markdown_category(self, title: str, filename: str) -> str:
        """Determine category from markdown section title"""
        title_lower = title.lower()
        filename_lower = filename.lower()
        
        # Life areas mapping
        life_areas = {
            'health': 'health_fitness',
            'fitness': 'health_fitness',
            'career': 'career',
            'character': 'character',
            'emotional': 'emotional',
            'spirituality': 'spirituality',
            'social': 'social_life',
            'finance': 'finance',
            'quality': 'quality_of_life',
            'house': 'house_environment',
            'intellectual': 'intellectual',
            'family': 'family'
        }
        
        for keyword, category in life_areas.items():
            if keyword in title_lower or keyword in filename_lower:
                return category
        
        return 'general'
    
    def _format_csv_row_content(self, row: pd.Series, category: str) -> str:
        """Format CSV row into readable content"""
        content_parts = []
        
        # Add category context
        content_parts.append(f"Category: {category}")
        
        # Format each column
        for col, value in row.items():
            if pd.notna(value) and str(value).strip():
                content_parts.append(f"{col}: {value}")
        
        return "\n".join(content_parts)
    
    def _extract_importance(self, row: pd.Series) -> str:
        """Extract importance level from row"""
        importance_cols = ['importance', 'wichtigkeit', 'priority', 'prio']
        for col in row.index:
            if col.lower() in importance_cols:
                return str(row[col]) if pd.notna(row[col]) else ""
        return ""
    
    def _extract_timeframe(self, row: pd.Series) -> str:
        """Extract timeframe from row"""
        timeframe_cols = ['timeframe', 'zeitrahmen', 'duration', 'when']
        for col in row.index:
            if col.lower() in timeframe_cols:
                return str(row[col]) if pd.notna(row[col]) else ""
        return ""
    
    def _extract_priority(self, row: pd.Series) -> str:
        """Extract priority from row"""
        priority_cols = ['priority', 'priorität', 'prio', 'importance']
        for col in row.index:
            if col.lower() in priority_cols:
                return str(row[col]) if pd.notna(row[col]) else ""
        return ""
    
    def get_documents_by_category(self, category: str) -> List[Document]:
        """Get all documents of a specific category"""
        return [doc for doc in self.documents if doc.category == category]
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        categories = {}
        total_words = 0
        
        for doc in self.documents:
            if doc.category not in categories:
                categories[doc.category] = 0
            categories[doc.category] += 1
            total_words += len(doc.content.split())
        
        return {
            'total_documents': len(self.documents),
            'categories': categories,
            'total_words': total_words,
            'avg_words_per_doc': total_words / len(self.documents) if self.documents else 0
        } 