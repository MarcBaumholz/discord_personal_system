"""
LLM Processor for Personal RSS News Bot.
Handles content analysis, relevance scoring, and summary generation using OpenRouter API.
"""

import os
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import re
from openai import OpenAI
import time

logger = logging.getLogger(__name__)


class LLMProcessor:
    """Handles LLM operations for content analysis and summarization."""
    
    def __init__(self, api_key: str = None, base_url: str = "https://openrouter.ai/api/v1",
                 primary_model: str = "meta-llama/llama-3.1-8b-instruct:free",
                 fallback_model: str = "meta-llama/llama-3.1-8b-instruct:free",
                 max_tokens: int = 1000, temperature: float = 0.3):
        """Initialize LLM processor with OpenRouter configuration."""
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.base_url = base_url
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. LLM features will be limited.")
        
        # Initialize OpenAI client for OpenRouter
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        ) if self.api_key else None
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
        # Topic keywords for relevance scoring
        self.topic_keywords = {
            'AI_LLM': [
                'artificial intelligence', 'AI', 'machine learning', 'ML', 'deep learning',
                'neural network', 'LLM', 'large language model', 'GPT', 'transformer',
                'natural language processing', 'NLP', 'computer vision', 'robotics',
                'automated', 'algorithm', 'model training', 'inference', 'OpenAI',
                'ChatGPT', 'Claude', 'Gemini', 'LLaMA', 'BERT', 'diffusion model'
            ],
            'PRODUCTIVITY': [
                'productivity', 'efficiency', 'workflow', 'time management', 'organization',
                'task management', 'project management', 'automation', 'optimization',
                'performance', 'focus', 'concentration', 'goal setting', 'planning',
                'prioritization', 'delegation', 'collaboration', 'remote work',
                'work-life balance', 'leadership', 'management', 'strategy'
            ],
            'COGNITIVE_SCIENCE': [
                'cognitive science', 'neuroscience', 'psychology', 'cognitive psychology',
                'brain', 'memory', 'learning', 'attention', 'perception', 'cognition',
                'consciousness', 'decision making', 'cognitive bias', 'mental model',
                'cognitive load', 'working memory', 'neurology', 'behavioral science',
                'cognitive function', 'brain imaging', 'neuroplasticity', 'mindfulness'
            ],
            'FLOW_PERFORMANCE': [
                'flow state', 'flow', 'peak performance', 'optimal experience', 'focus',
                'concentration', 'mindfulness', 'meditation', 'deep work', 'immersion',
                'intrinsic motivation', 'mastery', 'skill development', 'challenge',
                'engagement', 'attention training', 'mental training', 'performance',
                'excellence', 'expertise', 'deliberate practice', 'zone'
            ],
            'AUTOMATION': [
                'automation', 'automated', 'workflow automation', 'process automation',
                'RPA', 'robotic process automation', 'AI automation', 'scripting',
                'integration', 'API', 'webhook', 'no-code', 'low-code', 'IFTTT',
                'Zapier', 'personal assistant', 'virtual assistant', 'bot', 'scheduler',
                'smart home', 'IoT', 'automated systems', 'tool integration'
            ]
        }
    
    async def analyze_article_relevance(self, article: Dict) -> float:
        """
        Analyze article relevance to our topic areas.
        Returns relevance score between 0.0 and 1.0.
        """
        try:
            # First, try keyword-based scoring (fast, no API cost)
            keyword_score = self._calculate_keyword_relevance(article)
            
            # If keyword score is very low or high, we might not need LLM
            if keyword_score < 0.2:
                logger.debug(f"Low keyword score ({keyword_score:.2f}) for: {article['title']}")
                return keyword_score
            
            # Use LLM for more nuanced analysis if available
            if self.client and keyword_score >= 0.3:
                llm_score = await self._llm_relevance_analysis(article)
                if llm_score is not None:
                    # Combine keyword and LLM scores (weighted average)
                    final_score = (keyword_score * 0.4) + (llm_score * 0.6)
                    return min(1.0, final_score)
            
            return keyword_score
            
        except Exception as e:
            logger.error(f"Error analyzing relevance for {article['title']}: {e}")
            return 0.5  # Default moderate relevance
    
    def _calculate_keyword_relevance(self, article: Dict) -> float:
        """Calculate relevance based on keyword matching."""
        text_content = f"{article.get('title', '')} {article.get('content_summary', '')}"
        text_content = text_content.lower()
        
        total_score = 0.0
        category_matches = {}
        
        # Check each category
        for category, keywords in self.topic_keywords.items():
            score = 0.0
            matches = 0
            
            for keyword in keywords:
                if keyword.lower() in text_content:
                    # Weight longer keywords more heavily
                    weight = len(keyword.split())
                    score += weight
                    matches += 1
            
            if matches > 0:
                # Normalize by number of keywords in category
                category_score = min(1.0, score / len(keywords) * 10)
                category_matches[category] = category_score
                total_score += category_score
        
        # Apply category weights from config
        category_weights = {
            'AI_LLM': 0.30,
            'PRODUCTIVITY': 0.25,
            'COGNITIVE_SCIENCE': 0.20,
            'AUTOMATION': 0.15,
            'FLOW_PERFORMANCE': 0.10
        }
        
        weighted_score = 0.0
        for category, score in category_matches.items():
            weight = category_weights.get(category, 0.1)
            weighted_score += score * weight
        
        return min(1.0, weighted_score)
    
    async def _llm_relevance_analysis(self, article: Dict) -> Optional[float]:
        """Use LLM to analyze article relevance more deeply."""
        try:
            await self._rate_limit()
            
            prompt = self._create_relevance_prompt(article)
            
            response = self.client.chat.completions.create(
                model=self.primary_model,
                messages=[
                    {"role": "system", "content": "You are an expert content curator specializing in productivity, AI/LLM, cognitive science, flow states, and automation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract score from response
            score_match = re.search(r'(\d+(?:\.\d+)?)', response_text)
            if score_match:
                score = float(score_match.group(1))
                if score > 10:  # Assume it's out of 100
                    score = score / 100
                elif score > 1:  # Assume it's out of 10
                    score = score / 10
                return min(1.0, max(0.0, score))
            
            return None
            
        except Exception as e:
            logger.error(f"LLM relevance analysis failed: {e}")
            return None
    
    def _create_relevance_prompt(self, article: Dict) -> str:
        """Create prompt for relevance analysis."""
        return f"""
Analyze the relevance of this article to these topic areas:
1. AI & LLM (30% weight) - Artificial intelligence, machine learning, language models
2. Productivity (25% weight) - Personal productivity, efficiency, time management
3. Cognitive Science (20% weight) - Brain research, psychology, learning, memory
4. Automation (15% weight) - Workflow automation, tools, integrations
5. Flow & Performance (10% weight) - Peak performance, focus, flow states

Article:
Title: {article.get('title', '')}
Summary: {article.get('content_summary', '')[:200]}...

Rate the overall relevance on a scale of 0.0 to 1.0 where:
- 0.0-0.3: Not relevant or tangentially related
- 0.4-0.6: Moderately relevant, some useful insights
- 0.7-0.9: Highly relevant, valuable content
- 1.0: Extremely relevant, must-read content

Respond with just the numeric score (e.g., 0.75).
"""
    
    async def generate_article_summary(self, article: Dict) -> Optional[str]:
        """Generate a concise summary of an article using LLM."""
        try:
            if not self.client:
                return self._create_fallback_summary(article)
            
            await self._rate_limit()
            
            prompt = self._create_summary_prompt(article)
            
            response = self.client.chat.completions.create(
                model=self.primary_model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating concise, actionable summaries of articles about productivity, AI, cognitive science, and automation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return self._create_fallback_summary(article)
    
    def _create_summary_prompt(self, article: Dict) -> str:
        """Create prompt for article summarization."""
        return f"""
Summarize this article in 2-3 sentences, focusing on:
1. The main insight or discovery
2. Practical implications or applications
3. Why it matters for productivity, learning, or personal development

Article:
Title: {article.get('title', '')}
Content: {article.get('content_summary', '')[:500]}

Create a concise, actionable summary:
"""
    
    def _create_fallback_summary(self, article: Dict) -> str:
        """Create a basic summary without LLM."""
        content = article.get('content_summary', '')
        if len(content) > 150:
            # Take first sentence or first 150 characters
            sentences = content.split('. ')
            if sentences:
                return sentences[0] + '.'
            else:
                return content[:150] + '...'
        return content
    
    async def generate_weekly_summary(self, articles: List[Dict]) -> Optional[str]:
        """Generate a comprehensive weekly summary from selected articles."""
        try:
            if not self.client or not articles:
                return self._create_fallback_weekly_summary(articles)
            
            await self._rate_limit()
            
            # Group articles by category
            categorized_articles = self._categorize_articles(articles)
            
            prompt = self._create_weekly_summary_prompt(categorized_articles)
            
            response = self.client.chat.completions.create(
                model=self.primary_model,
                messages=[
                    {"role": "system", "content": "You are an expert newsletter writer who creates engaging weekly summaries of the latest developments in AI, productivity, cognitive science, and automation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            logger.error(f"Weekly summary generation failed: {e}")
            return self._create_fallback_weekly_summary(articles)
    
    def _categorize_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Group articles by category."""
        categorized = {}
        for article in articles:
            category = article.get('category', 'OTHER')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(article)
        return categorized
    
    def _create_weekly_summary_prompt(self, categorized_articles: Dict[str, List[Dict]]) -> str:
        """Create prompt for weekly summary generation."""
        article_content = ""
        
        for category, articles in categorized_articles.items():
            article_content += f"\n## {category.replace('_', ' ').title()}\n"
            for i, article in enumerate(articles[:3], 1):  # Limit to top 3 per category
                article_content += f"{i}. **{article['title']}**\n"
                article_content += f"   Source: {article['source']}\n"
                article_content += f"   Summary: {article.get('content_summary', '')[:200]}...\n\n"
        
        return f"""
Create an engaging weekly newsletter summary from these articles. Structure it as:

1. **Weekly Highlights** - Brief overview of key themes
2. **AI & Technology Updates** - Latest in AI, LLMs, and tech
3. **Productivity Insights** - Tips and strategies for better performance
4. **Research & Science** - Cognitive science and learning research
5. **Tools & Automation** - New tools and automation opportunities
6. **Key Takeaways** - 3-5 actionable insights

Make it engaging, informative, and actionable. Include relevant article titles and sources.

Articles to summarize:
{article_content}

Write a newsletter-style summary (800-1200 words):
"""
    
    def _create_fallback_weekly_summary(self, articles: List[Dict]) -> str:
        """Create a basic weekly summary without LLM."""
        if not articles:
            return "No articles found for this week's summary."
        
        summary = f"# Weekly Summary - {datetime.now().strftime('%B %d, %Y')}\n\n"
        summary += f"This week we've curated {len(articles)} articles across our key interest areas.\n\n"
        
        # Group by category
        categorized = self._categorize_articles(articles)
        
        for category, category_articles in categorized.items():
            category_name = category.replace('_', ' ').title()
            summary += f"## {category_name}\n"
            
            for article in category_articles[:3]:  # Top 3 per category
                summary += f"- **{article['title']}** ({article['source']})\n"
                summary += f"  {article.get('content_summary', '')[:100]}...\n\n"
        
        summary += "## Key Themes\n"
        summary += "- Latest developments in AI and machine learning\n"
        summary += "- Productivity and performance optimization strategies\n"
        summary += "- Cognitive science insights for better learning\n"
        summary += "- Automation tools and workflow improvements\n"
        
        return summary
    
    async def _rate_limit(self):
        """Implement rate limiting for API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def batch_analyze_articles(self, articles: List[Dict], 
                              max_concurrent: int = 3) -> List[Dict]:
        """Analyze multiple articles for relevance in batches."""
        async def analyze_batch():
            semaphore = asyncio.Semaphore(max_concurrent)
            tasks = []
            
            async def analyze_single(article):
                async with semaphore:
                    relevance_score = await self.analyze_article_relevance(article)
                    article['relevance_score'] = relevance_score
                    return article
            
            for article in articles:
                task = asyncio.create_task(analyze_single(article))
                tasks.append(task)
            
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Run the batch analysis
        try:
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(analyze_batch())
            
            # Filter out exceptions
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Article analysis failed: {result}")
                else:
                    valid_results.append(result)
            
            return valid_results
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return articles


# Utility functions
def load_llm_config() -> Dict:
    """Load LLM configuration from environment or defaults."""
    return {
        'api_key': os.getenv('OPENROUTER_API_KEY'),
        'primary_model': os.getenv('LLM_PRIMARY_MODEL', 'meta-llama/llama-3.1-8b-instruct:free'),
        'fallback_model': os.getenv('LLM_FALLBACK_MODEL', 'meta-llama/llama-3.1-8b-instruct:free'),
        'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '1000')),
        'temperature': float(os.getenv('LLM_TEMPERATURE', '0.3'))
    }


async def test_llm_processor():
    """Test function for LLM processor."""
    logging.basicConfig(level=logging.INFO)
    
    # Test article
    test_article = {
        'title': 'New Advances in Large Language Models for Productivity Applications',
        'content_summary': 'Recent research shows that LLMs can significantly improve productivity through better task automation and intelligent assistance. The study demonstrates how GPT-4 and similar models can be integrated into workflows to enhance efficiency and reduce cognitive load.',
        'source': 'AI Research Journal',
        'category': 'AI_LLM'
    }
    
    config = load_llm_config()
    processor = LLMProcessor(**config)
    
    # Test relevance analysis
    relevance = await processor.analyze_article_relevance(test_article)
    print(f"Relevance score: {relevance:.2f}")
    
    # Test summary generation
    summary = await processor.generate_article_summary(test_article)
    print(f"Summary: {summary}")


if __name__ == "__main__":
    asyncio.run(test_llm_processor()) 