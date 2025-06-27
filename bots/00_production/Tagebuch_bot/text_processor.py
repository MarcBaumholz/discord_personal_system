"""
Text Processor for Tagebuch Bot
Handles title generation and text processing for journal entries.
"""

import re
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger('tagebuch_bot.text_processor')

class TextProcessor:
    """Handles text processing and title generation for journal entries"""
    
    def __init__(self, max_title_length: int = 50):
        """
        Initialize text processor
        
        Args:
            max_title_length: Maximum length for generated titles
        """
        self.max_title_length = max_title_length
    
    def generate_title(self, text: str) -> str:
        """
        Generate a title from journal entry text
        
        Args:
            text: The journal entry text
            
        Returns:
            str: Generated title
        """
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            
            if not cleaned_text:
                return self._generate_date_title()
            
            # Try to extract title from first sentence
            title = self._extract_title_from_first_sentence(cleaned_text)
            
            if not title or len(title.strip()) < 3:
                # Fallback to key phrases
                title = self._extract_key_phrases(cleaned_text)
            
            if not title or len(title.strip()) < 3:
                # Final fallback to date-based title
                title = self._generate_date_title()
            
            # Ensure title is within length limit
            if len(title) > self.max_title_length:
                title = title[:self.max_title_length-3] + "..."
            
            logger.info(f"Generated title: '{title}' from text length: {len(text)}")
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return self._generate_date_title()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove Discord mentions, links, and formatting
        cleaned = re.sub(r'<@[!&]?\d+>', '', cleaned)  # User/role mentions
        cleaned = re.sub(r'<#\d+>', '', cleaned)       # Channel mentions
        cleaned = re.sub(r'https?://\S+', '', cleaned) # URLs
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # Bold
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)      # Italic
        cleaned = re.sub(r'__([^_]+)__', r'\1', cleaned)      # Underline
        
        return cleaned.strip()
    
    def _extract_title_from_first_sentence(self, text: str) -> str:
        """Extract title from the first sentence"""
        # Find first sentence ending with punctuation
        sentence_match = re.match(r'^([^.!?;]+[.!?;])', text)
        
        if sentence_match:
            sentence = sentence_match.group(1).strip()
            # Remove the punctuation at the end
            sentence = sentence.rstrip('.!?;')
            # Remove common journal starters
            sentence = re.sub(r'^(heute|heute war|ich habe|mein tag|der tag)', '', sentence, flags=re.IGNORECASE)
            return sentence.strip()
        
        # If no sentence ending found, take first 50 characters
        words = text.split()
        if len(words) > 0:
            title_words = []
            char_count = 0
            for word in words:
                if char_count + len(word) + 1 > self.max_title_length:
                    break
                title_words.append(word)
                char_count += len(word) + 1
            
            return ' '.join(title_words)
        
        return ""
    
    def _extract_key_phrases(self, text: str) -> str:
        """Extract key phrases from text"""
        # Look for emotional keywords or important phrases
        key_patterns = [
            r'(heute.*?war.*?(?:toll|schön|gut|schlecht|schwer|anstrengend))',
            r'(ich.*?bin.*?(?:glücklich|traurig|müde|aufgeregt|dankbar))',
            r'(es.*?war.*?ein.*?(?:guter|schlechter|interessanter|besonderer) Tag)',
        ]
        
        for pattern in key_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                phrase = match.group(1).strip()
                if len(phrase) <= self.max_title_length:
                    return phrase
        
        # Fallback: use first few words
        words = text.split()[:5]
        return ' '.join(words) if words else ""
    
    def _generate_date_title(self) -> str:
        """Generate a date-based title as fallback"""
        today = datetime.now()
        return f"Tagebuch {today.strftime('%d.%m.%Y')}"
    
    def validate_text(self, text: str) -> bool:
        """
        Validate if text is suitable for journal entry
        
        Args:
            text: Text to validate
            
        Returns:
            bool: True if text is valid for journal entry
        """
        if not text or not text.strip():
            return False
        
        # Must be at least 10 characters after cleaning
        cleaned = self._clean_text(text)
        if len(cleaned) < 10:
            return False
        
        # Should contain at least one alphabetic character
        if not re.search(r'[a-zA-ZäöüÄÖÜß]', cleaned):
            return False
        
        return True
    
    def format_text_for_notion(self, text: str) -> str:
        """
        Format text for storage in Notion
        
        Args:
            text: Raw text to format
            
        Returns:
            str: Formatted text for Notion
        """
        # Clean text but preserve basic formatting
        formatted = text.strip()
        
        # Normalize line breaks
        formatted = re.sub(r'\r\n|\r', '\n', formatted)
        
        # Remove excessive whitespace but preserve paragraph breaks
        formatted = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted)
        
        return formatted 