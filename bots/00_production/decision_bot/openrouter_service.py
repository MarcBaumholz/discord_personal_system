import os
import logging
import asyncio
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('decision_bot.openrouter_service')

class OpenRouterService:
    """Service to interact with OpenRouter LLM API for decision analysis"""
    
    def __init__(self):
        """Initialize OpenRouter service"""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY not found in environment variables")
            raise ValueError("OpenRouter API key is required")
        
        logger.info("OpenRouter Service initialized successfully")
    
    async def analyze_decision(self, question: str, user_data_summary: str) -> Optional[str]:
        """Analyze a decision question against user's personal data (legacy method)
        
        Args:
            question: The decision question from the user
            user_data_summary: Summary of user's values, goals, and personal data
            
        Returns:
            Formatted analysis response or None if failed
        """
        return await self.analyze_decision_with_context(question, user_data_summary)
    
    async def analyze_decision_with_context(self, question: str, context: str) -> Optional[str]:
        """Analyze a decision question with enhanced RAG context
        
        Args:
            question: The decision question from the user
            context: Enhanced context from RAG system or CSV data
            
        Returns:
            Formatted analysis response or None if failed
        """
        try:
            prompt = self._build_enhanced_analysis_prompt(question, context)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek/deepseek-r1",
                "messages": [
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            response = await self._async_post_request(self.api_url, headers, payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    analysis = result['choices'][0]['message']['content']
                    return self._format_discord_response(analysis)
                else:
                    logger.error("No choices in OpenRouter response")
                    return None
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing decision: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the decision coach"""
        return """You are a wise and empathetic decision coach who analyzes life choices against personal values, goals, and authentic self. Your expertise includes:

- Deep understanding of human psychology and decision-making
- Ability to synthesize complex personal data into actionable insights
- Expertise in values-based decision making
- Knowledge of goal alignment and life satisfaction
- Skill in identifying potential blind spots and biases

Your analysis should be:
- Thoughtful and evidence-based using the provided personal context
- Actionable with concrete next steps
- Empathetic yet honest about potential challenges
- Structured and easy to understand
- Written in German with emojis for better readability

Always ground your advice in the specific personal data provided, referencing concrete values, goals, and experiences when relevant."""
    
    def _build_enhanced_analysis_prompt(self, question: str, context: str) -> str:
        """Build enhanced prompt for RAG-powered decision analysis
        
        Args:
            question: User's decision question
            context: Enhanced context from RAG system
            
        Returns:
            Optimized prompt for the LLM
        """
        prompt = f"""Als erfahrener Entscheidungscoach analysiere ich die folgende Frage anhand der umfassenden persönlichen Daten des Nutzers:

**ENTSCHEIDUNGSFRAGE:**
{question}

**PERSÖNLICHER KONTEXT DES NUTZERS:**
{context}

**ANALYSE-AUFTRAG:**
Führe eine tiefgreifende Entscheidungsanalyse durch, die sich konkret auf die bereitgestellten persönlichen Daten bezieht. Strukturiere deine Antwort exakt wie folgt:

🎯 **ALIGNMENT-ANALYSE**
- Werte-Übereinstimmung: [X/10] mit konkreter Begründung
- Ziele-Übereinstimmung: [X/10] mit Bezug zu spezifischen Zielen  
- Identitäts-Übereinstimmung: [X/10] basierend auf Persönlichkeitsmerkmalen

🧠 **DETAILLIERTE BEGRÜNDUNG**
- Direkte Bezüge zu konkreten Werten aus den Daten
- Verbindungen zu spezifischen Zielen und deren Zeitrahmen
- Konfliktpunkte mit dokumentierten Werten oder Zielen
- Relevante Erkenntnisse aus Lebensbereichen (Gesundheit, Karriere, etc.)

⚡ **HANDLUNGSEMPFEHLUNGEN**
- 3-5 konkrete, sofort umsetzbare Schritte
- Priorisierung basierend auf Wichtigkeit in den persönlichen Daten
- Spezifische Überlegungen oder Recherche-Empfehlungen

💭 **REFLEXIONS-FRAGEN**
- 3-4 tiefgreifende Fragen zur Selbstreflexion
- Bezug zu dokumentierten Werten und Lebensbereichen
- Fragen zur langfristigen Auswirkung auf persönliche Ziele

⚠️ **RISIKO-NUTZEN-BEWERTUNG**
- Positive Auswirkungen auf spezifische Lebensbereiche
- Potenzielle Herausforderungen im Kontext der persönlichen Situation
- Langfristige Konsequenzen für dokumentierte Ziele

**WICHTIGE ANFORDERUNGEN:**
- Verwende spezifische Details aus den bereitgestellten persönlichen Daten
- Zitiere konkrete Werte, Ziele oder Lebensbereiche wenn relevant
- Mache die Analyse so persönlich und maßgeschneidert wie möglich
- Berücksichtige verschiedene Lebensbereiche (Gesundheit, Karriere, Beziehungen, etc.)
- Biete sowohl emotionale als auch rationale Perspektiven"""

        return prompt
    
    def _build_decision_analysis_prompt(self, question: str, user_data: str) -> str:
        """Build the prompt for decision analysis (legacy method)
        
        Args:
            question: User's decision question
            user_data: User's personal data summary
            
        Returns:
            Formatted prompt for the LLM
        """
        return self._build_enhanced_analysis_prompt(question, user_data)
    
    def _format_discord_response(self, analysis: str) -> str:
        """Format the analysis response for Discord with enhanced formatting
        
        Args:
            analysis: Raw analysis from LLM
            
        Returns:
            Discord-formatted response with proper structure
        """
        try:
            # Ensure proper Discord markdown formatting
            formatted = analysis.replace("**", "**").replace("*", "*")
            
            # Add header if not present
            if not any(emoji in formatted for emoji in ["🎯", "🧠", "⚡", "💭", "⚠️"]):
                formatted = "🎯 **PERSONALISIERTE ENTSCHEIDUNGS-ANALYSE**\n\n" + formatted
            
            # Ensure proper spacing for Discord
            formatted = formatted.replace("\n\n", "\n\n")
            
            # Add contextual footer
            footer_options = [
                "💡 *Diese Analyse basiert auf deinen persönlichen Werten, Zielen und Lebensdaten.*",
                "🧠 *Analysiert mit deinen individuellen Daten für maximale Relevanz.*",
                "⭐ *Maßgeschneiderte Empfehlungen basierend auf deinem persönlichen Profil.*"
            ]
            
            # Choose footer based on content analysis
            if "RAG" in analysis or "RELEVANT" in analysis:
                footer = footer_options[1]  # RAG-specific
            elif "Werte" in analysis and "Ziele" in analysis:
                footer = footer_options[0]  # Values and goals
            else:
                footer = footer_options[2]  # General personalization
            
            formatted += f"\n\n{footer}"
            
            # Ensure Discord character limits
            if len(formatted) > 2000:
                # Split long responses
                formatted = self._split_long_response(formatted)
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting Discord response: {e}")
            return analysis  # Return unformatted if formatting fails
    
    def _split_long_response(self, response: str) -> str:
        """Split long responses for Discord character limit
        
        Args:
            response: The full response text
            
        Returns:
            Truncated response with indication of truncation
        """
        try:
            if len(response) <= 2000:
                return response
            
            # Find a good break point (after a section)
            sections = ["🧠 **DETAILLIERTE BEGRÜNDUNG**", "⚡ **HANDLUNGSEMPFEHLUNGEN**", 
                       "💭 **REFLEXIONS-FRAGEN**", "⚠️ **RISIKO-NUTZEN-BEWERTUNG**"]
            
            for section in sections:
                section_pos = response.find(section)
                if section_pos > 0 and section_pos < 1800:  # Safe margin
                    truncated = response[:section_pos]
                    truncated += "\n\n📝 *Antwort gekürzt - verwende eine spezifischere Frage für Details.*"
                    return truncated
            
            # Fallback: Cut at word boundary
            truncated = response[:1900]
            last_space = truncated.rfind(' ')
            if last_space > 1500:
                truncated = truncated[:last_space]
            
            truncated += "\n\n📝 *Antwort gekürzt - verwende eine spezifischere Frage für Details.*"
            return truncated
            
        except Exception as e:
            logger.error(f"Error splitting long response: {e}")
            return response[:1950] + "\n\n📝 *Antwort gekürzt.*"
    
    async def _async_post_request(self, url: str, headers: Dict[str, str], json_data: Dict[str, Any]) -> requests.Response:
        """Make an async POST request to the API
        
        Args:
            url: API endpoint URL
            headers: Request headers
            json_data: JSON payload
            
        Returns:
            Response object
        """
        try:
            # Use asyncio to run the synchronous request in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(url, headers=headers, json=json_data, timeout=30)
            )
            return response
            
        except Exception as e:
            logger.error(f"Error making async POST request: {e}")
            # Return a mock response object for error handling
            class MockResponse:
                def __init__(self):
                    self.status_code = 500
                    self.text = str(e)
                def json(self):
                    return {"error": str(e)}
            return MockResponse() 