import logging
from typing import Dict, Any, Optional

from csv_data_loader import CSVDataLoader
from openrouter_service import OpenRouterService

# RAG system imports (will be created)
try:
    from rag_system import RAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logging.warning("RAG system not available - falling back to basic CSV analysis")

logger = logging.getLogger('decision_bot.decision_analyzer')

class DecisionAnalyzer:
    """Enhanced decision analysis engine that combines user data with RAG-powered LLM analysis"""
    
    def __init__(self, upload_folder: str = "./upload"):
        """Initialize the decision analyzer
        
        Args:
            upload_folder: Path to folder containing user CSV files and documents
        """
        self.upload_folder = upload_folder
        self.csv_loader = CSVDataLoader(upload_folder)
        self.openrouter_service = OpenRouterService()
        
        # Initialize RAG system if available
        self.rag_system = None
        self.rag_enabled = False
        
        if RAG_AVAILABLE:
            try:
                self.rag_system = RAGSystem(
                    upload_folder=upload_folder,
                    model_name="all-MiniLM-L6-v2",  # Free HuggingFace model
                    index_path="./vector_index"
                )
                logger.info("RAG system initialized")
            except Exception as e:
                logger.error(f"Failed to initialize RAG system: {e}")
                self.rag_system = None
        
        self.user_data_loaded = False
        logger.info("Decision Analyzer initialized with RAG support" if self.rag_system else "Decision Analyzer initialized (CSV only)")
    
    async def initialize(self) -> bool:
        """Initialize and load user data from CSV files and RAG system
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Loading user data from CSV files...")
            user_data = self.csv_loader.load_all_data()
            
            csv_loaded = bool(user_data)
            if csv_loaded:
                logger.info("CSV data loaded successfully")
            else:
                logger.warning("No CSV data loaded")
            
            # Initialize RAG system if available
            rag_loaded = False
            if self.rag_system:
                try:
                    logger.info("Initializing RAG system...")
                    rag_loaded = await self.rag_system.initialize()
                    if rag_loaded:
                        self.rag_enabled = True
                        logger.info("RAG system initialized successfully")
                    else:
                        logger.warning("RAG system initialization failed")
                except Exception as e:
                    logger.error(f"RAG system initialization error: {e}")
            
            # Consider initialization successful if either CSV or RAG loaded
            self.user_data_loaded = csv_loaded or rag_loaded
            
            if self.user_data_loaded:
                logger.info("Decision analyzer initialization completed")
                return True
            else:
                logger.warning("No user data loaded from any source")
                return False
            
        except Exception as e:
            logger.error(f"Error initializing decision analyzer: {e}")
            self.user_data_loaded = False
            return False
    
    async def analyze_question(self, question: str) -> Optional[str]:
        """Analyze a decision question against user's personal data using RAG + LLM
        
        Args:
            question: The decision question from the user
            
        Returns:
            Formatted analysis response or error message
        """
        try:
            # Ensure user data is loaded
            if not self.user_data_loaded:
                if not await self.initialize():
                    return self._create_no_data_response()
            
            logger.info(f"Analyzing question: {question[:100]}...")
            
            # Get context using RAG system (enhanced) or CSV data (fallback)
            if self.rag_enabled and self.rag_system:
                context = await self._get_rag_enhanced_context(question)
                logger.info("Using RAG-enhanced context for analysis")
            else:
                context = self._get_csv_context()
                logger.info("Using CSV-based context for analysis")
            
            if not context or context.strip() == "No user data available.":
                return self._create_no_data_response()
            
            # Analyze with OpenRouter using enhanced context
            analysis = await self.openrouter_service.analyze_decision_with_context(question, context)
            
            if analysis:
                logger.info("Decision analysis completed successfully")
                return analysis
            else:
                logger.error("Failed to get analysis from OpenRouter")
                return self._create_error_response()
                
        except Exception as e:
            logger.error(f"Error analyzing question: {e}")
            return self._create_error_response(str(e))
    
    async def _get_rag_enhanced_context(self, question: str) -> str:
        """Get enhanced context using RAG system
        
        Args:
            question: The decision question
            
        Returns:
            Comprehensive context string
        """
        try:
            context_parts = []
            
            # Get relevant context from RAG system (most important)
            rag_context = self.rag_system.get_relevant_context(question, max_context_length=1500)
            if rag_context:
                context_parts.append("=== RELEVANT PERSONAL CONTEXT ===")
                context_parts.append(rag_context)
            
            # Get specific values and goals context
            values_context = self.rag_system.get_values_context(question)
            if values_context:
                context_parts.append("\n=== RELEVANT VALUES ===")
                context_parts.append(values_context)
            
            goals_context = self.rag_system.get_goals_context(question)
            if goals_context:
                context_parts.append("\n=== RELEVANT GOALS ===")
                context_parts.append(goals_context)
            
            # Add CSV summary as backup
            csv_summary = self.csv_loader.get_user_summary()
            if csv_summary and csv_summary != "No user data available.":
                context_parts.append("\n=== ADDITIONAL DATA SUMMARY ===")
                context_parts.append(csv_summary)
            
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {e}")
            # Fallback to CSV context
            return self._get_csv_context()
    
    def _get_csv_context(self) -> str:
        """Get context from CSV data (fallback method)
        
        Returns:
            CSV-based context string
        """
        return self.csv_loader.get_user_summary()
    
    def _create_no_data_response(self) -> str:
        """Create response when no user data is available"""
        return """🤖 **Keine persönlichen Daten gefunden**

Um dir bei Entscheidungen zu helfen, benötige ich deine persönlichen Daten.

📁 **Unterstützte Dateiformate:**
**CSV-Dateien:**
- `values.csv` - Deine Werte und Prinzipien
- `goals.csv` - Deine Ziele und Aspirationen  
- `identity.csv` - Deine Identität und Persönlichkeit
- `experiences.csv` - Wichtige Erfahrungen und Lektionen

**Markdown-Dateien:**
- `life_content.md` - Detaillierte Lebensbereiche
- `me_content.md` - Persönliche Informationen
- Weitere `.md` Dateien mit persönlichen Inhalten

📝 **CSV-Format Beispiel:**
```
Category,Description,Importance
Value,Familie an erster Stelle,Hoch
Value,Authentizität leben,Hoch
Goal,Gesund und fit bleiben,Mittel
```

🧠 **Mit RAG-System:** Ich kann auch aus umfangreichen Markdown-Inhalten relevante Informationen intelligent abrufen!

Lade deine Daten in den `/upload` Ordner hoch und stelle deine Frage erneut! 🚀"""
    
    def _create_error_response(self, error_detail: str = None) -> str:
        """Create response for analysis errors
        
        Args:
            error_detail: Optional error details
            
        Returns:
            Formatted error response
        """
        base_response = """⚠️ **Fehler bei der Analyse**

Es gab ein Problem bei der Analyse deiner Entscheidung. Bitte versuche es in einigen Minuten erneut.

🔧 **Mögliche Lösungen:**
- Stelle sicher, dass deine Dateien im `/upload` Ordner sind
- Überprüfe, ob deine Frage klar formuliert ist
- Versuche es mit einer einfacheren Frage
- Bei RAG-Fehlern: Verwende `!reload` um das System neu zu starten

💬 Wenn das Problem weiterhin besteht, formuliere deine Frage anders oder kontaktiere den Support."""
        
        if error_detail:
            base_response += f"\n\n🔍 **Technische Details:** {error_detail}"
        
        return base_response
    
    def get_user_data_status(self) -> Dict[str, Any]:
        """Get status information about loaded user data including RAG system
        
        Returns:
            Dictionary with comprehensive data status information
        """
        try:
            status = {
                'loaded': self.user_data_loaded,
                'csv_loaded': False,
                'rag_enabled': self.rag_enabled,
                'files_found': 0,
                'categories': []
            }
            
            # CSV data status
            if self.user_data_loaded:
                user_data = self.csv_loader.user_data
                categories = []
                
                if user_data.get('values'):
                    categories.append(f"Values ({len(user_data['values'])} items)")
                if user_data.get('goals'):
                    categories.append(f"Goals ({len(user_data['goals'])} items)")
                if user_data.get('identity'):
                    categories.append(f"Identity ({len(user_data['identity'])} items)")
                if user_data.get('experiences'):
                    categories.append(f"Experiences ({len(user_data['experiences'])} items)")
                if user_data.get('preferences'):
                    categories.append(f"Preferences ({len(user_data['preferences'])} items)")
                
                status['csv_loaded'] = bool(categories)
                status['files_found'] = len(user_data.get('raw_data', {}))
                status['categories'].extend(categories)
            
            # RAG system status
            if self.rag_enabled and self.rag_system:
                rag_stats = self.rag_system.get_system_stats()
                status['rag_documents'] = rag_stats.get('total_documents', 0)
                status['rag_categories'] = list(rag_stats.get('doc_categories', {}).keys())
                
                # Add RAG categories to main categories list
                for cat, count in rag_stats.get('doc_categories', {}).items():
                    status['categories'].append(f"RAG-{cat} ({count} chunks)")
            
            # Overall status message
            if status['csv_loaded'] and status['rag_enabled']:
                status['message'] = 'Enhanced analysis with CSV + RAG system'
            elif status['rag_enabled']:
                status['message'] = 'RAG-powered analysis (no CSV)'
            elif status['csv_loaded']:
                status['message'] = 'Basic CSV analysis (no RAG)'
            else:
                status['message'] = 'No user data loaded'
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting user data status: {e}")
            return {
                'loaded': False,
                'csv_loaded': False,
                'rag_enabled': False,
                'message': f'Error accessing user data: {str(e)}',
                'files_found': 0,
                'categories': []
            }
    
    async def reload_data(self) -> bool:
        """Reload all data sources (CSV + RAG)
        
        Returns:
            True if reload successful
        """
        try:
            logger.info("Reloading all data sources...")
            
            # Reset state
            self.user_data_loaded = False
            self.rag_enabled = False
            
            # Reload CSV data
            self.csv_loader = CSVDataLoader(self.upload_folder)
            
            # Reload RAG system
            if self.rag_system:
                success = await self.rag_system.reload_data()
                if success:
                    self.rag_enabled = True
            
            # Reinitialize
            return await self.initialize()
            
        except Exception as e:
            logger.error(f"Error reloading data: {e}")
            return False
    
    def get_status_report(self) -> str:
        """Get a comprehensive status report including RAG system
        
        Returns:
            Formatted status report string
        """
        status = self.get_user_data_status()
        
        if not status['loaded']:
            return "🤖 Decision Analyzer: ❌ No data loaded"
        
        report_lines = [
            "🧠 Decision Analyzer Status Report",
            "=" * 35
        ]
        
        # CSV status
        if status['csv_loaded']:
            report_lines.append(f"📄 CSV Data: ✅ {status['files_found']} files loaded")
        else:
            report_lines.append("📄 CSV Data: ❌ No CSV files")
        
        # RAG status
        if status['rag_enabled']:
            rag_docs = status.get('rag_documents', 0)
            report_lines.append(f"🧠 RAG System: ✅ {rag_docs} document chunks indexed")
            if status.get('rag_categories'):
                report_lines.append(f"📊 RAG Categories: {', '.join(status['rag_categories'])}")
        else:
            report_lines.append("🧠 RAG System: ❌ Not available")
        
        # Categories
        if status['categories']:
            report_lines.append(f"📋 Available Data: {', '.join(status['categories'])}")
        
        # Overall capability
        report_lines.append(f"⚡ Analysis Mode: {status['message']}")
        
        return "\n".join(report_lines) 