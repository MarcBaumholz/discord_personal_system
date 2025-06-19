import os
import random
from pathlib import Path
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / 'data'

def load_all_md_content() -> List[Tuple[str, str]]:
    """
    Load all MD files from the data directory and return them as chunks.
    
    Returns:
        List of tuples containing (title, content) pairs
    """
    documents = []
    
    for md_file in DATA_DIR.glob('*.md'):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content into manageable chunks
            chunks = split_content_into_chunks(content, md_file.stem)
            documents.extend(chunks)
            logger.info(f"Loaded {len(chunks)} chunks from {md_file.name}")
            
        except Exception as e:
            logger.error(f"Error loading {md_file}: {e}")
    
    return documents

def split_content_into_chunks(content: str, source: str, chunk_size: int = 1000) -> List[Tuple[str, str]]:
    """
    Split content into chunks for better RAG performance.
    
    Args:
        content: The content to split
        source: The source file name
        chunk_size: Maximum characters per chunk
        
    Returns:
        List of (title, chunk_content) tuples
    """
    chunks = []
    lines = content.split('\n')
    current_chunk = []
    current_size = 0
    chunk_number = 1
    current_title = source
    
    for line in lines:
        # Check if this is a new section (starts with #)
        if line.startswith('#'):
            # Save current chunk if it has content
            if current_chunk:
                chunk_content = '\n'.join(current_chunk).strip()
                if chunk_content:
                    chunks.append((f"{current_title} - Part {chunk_number}", chunk_content))
                    chunk_number += 1
                current_chunk = []
                current_size = 0
            
            # Update title for new section
            current_title = f"{source} - {line.strip('#').strip()}"
            current_chunk.append(line)
            current_size += len(line) + 1
        else:
            current_chunk.append(line)
            current_size += len(line) + 1
            
            # If chunk is getting too large, split it
            if current_size > chunk_size:
                chunk_content = '\n'.join(current_chunk).strip()
                if chunk_content:
                    chunks.append((f"{current_title} - Part {chunk_number}", chunk_content))
                    chunk_number += 1
                current_chunk = []
                current_size = 0
    
    # Add final chunk
    if current_chunk:
        chunk_content = '\n'.join(current_chunk).strip()
        if chunk_content:
            chunks.append((f"{current_title} - Part {chunk_number}", chunk_content))
    
    return chunks

def get_random_learning_content() -> Tuple[str, str]:
    """
    Get a random learning snippet from the loaded content.
    
    Returns:
        Tuple of (title, content)
    """
    try:
        all_content = load_all_md_content()
        if not all_content:
            return "No Learning Content", "No learning content available."
        
        title, content = random.choice(all_content)
        
        # Limit content length for Discord messages
        if len(content) > 1500:
            content = content[:1500] + "...\n\n*Content truncated. Use !ask for more details.*"
        
        return title, content
        
    except Exception as e:
        logger.error(f"Error getting random learning: {e}")
        return "Error", "Unable to load learning content." 