import os
import pandas as pd
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger('decision_bot.csv_data_loader')

class CSVDataLoader:
    """Loads and processes user personal data from CSV files"""
    
    def __init__(self, upload_folder: str = "./upload"):
        """Initialize the CSV data loader
        
        Args:
            upload_folder: Path to folder containing CSV files
        """
        self.upload_folder = upload_folder
        self.user_data = {}
        logger.info(f"Initialized CSV Data Loader for folder: {upload_folder}")
    
    def load_all_data(self) -> Dict[str, Any]:
        """Load all CSV files from upload folder and combine into user profile
        
        Returns:
            Dict containing combined user data from all CSV files
        """
        try:
            if not os.path.exists(self.upload_folder):
                logger.warning(f"Upload folder {self.upload_folder} does not exist")
                return {}
            
            csv_files = [f for f in os.listdir(self.upload_folder) if f.endswith('.csv')]
            
            if not csv_files:
                logger.warning(f"No CSV files found in {self.upload_folder}")
                return {}
            
            logger.info(f"Found {len(csv_files)} CSV files to process")
            
            combined_data = {
                'values': [],
                'goals': [],
                'identity': [],
                'experiences': [],
                'preferences': [],
                'raw_data': {}
            }
            
            for csv_file in csv_files:
                file_path = os.path.join(self.upload_folder, csv_file)
                file_data = self._load_single_csv(file_path)
                
                if file_data is not None and not file_data.empty:
                    combined_data['raw_data'][csv_file] = file_data
                    self._categorize_data(file_data, combined_data, csv_file)
            
            self.user_data = combined_data
            logger.info("Successfully loaded all CSV data")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            return {}
    
    def _load_single_csv(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load a single CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame containing the CSV data or None if failed
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            logger.info(f"Loaded {file_path}: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    def _categorize_data(self, df: pd.DataFrame, combined_data: Dict, filename: str):
        """Categorize data from DataFrame into user profile categories
        
        Args:
            df: DataFrame to categorize
            combined_data: Dictionary to add categorized data to
            filename: Name of the source file for context
        """
        try:
            # Convert DataFrame to text format for analysis
            text_content = self._dataframe_to_text(df, filename)
            
            # Categorize based on filename and content
            if any(keyword in filename.lower() for keyword in ['werte', 'values', 'principles']):
                combined_data['values'].extend(self._extract_values(df))
            elif any(keyword in filename.lower() for keyword in ['goals', 'ziele', 'objectives']):
                combined_data['goals'].extend(self._extract_goals(df))
            elif any(keyword in filename.lower() for keyword in ['identity', 'self', 'personality']):
                combined_data['identity'].extend(self._extract_identity(df))
            elif any(keyword in filename.lower() for keyword in ['experience', 'lessons', 'learning']):
                combined_data['experiences'].extend(self._extract_experiences(df))
            else:
                # General preferences or uncategorized data
                combined_data['preferences'].append({
                    'source': filename,
                    'content': text_content
                })
                
        except Exception as e:
            logger.error(f"Error categorizing data from {filename}: {e}")
    
    def _dataframe_to_text(self, df: pd.DataFrame, filename: str) -> str:
        """Convert DataFrame to readable text format
        
        Args:
            df: DataFrame to convert
            filename: Source filename for context
            
        Returns:
            Formatted text representation of the data
        """
        try:
            text_lines = [f"Data from {filename}:"]
            
            for index, row in df.iterrows():
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                if row_text.strip():
                    text_lines.append(f"- {row_text}")
            
            return "\n".join(text_lines)
            
        except Exception as e:
            logger.error(f"Error converting DataFrame to text: {e}")
            return f"Data from {filename} (conversion error)"
    
    def _extract_values(self, df: pd.DataFrame) -> List[str]:
        """Extract values from DataFrame"""
        values = []
        # Look for 'Description' column if it exists, or get all text content
        if 'Description' in df.columns:
            values.extend(df['Description'].dropna().astype(str).tolist())
        else:
            # If no Description column, get all text columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    values.extend(df[col].dropna().astype(str).tolist())
        return values
    
    def _extract_goals(self, df: pd.DataFrame) -> List[str]:
        """Extract goals from DataFrame"""
        goals = []
        # Look for 'Description' column if it exists, or get all text content
        if 'Description' in df.columns:
            goals.extend(df['Description'].dropna().astype(str).tolist())
        else:
            # If no Description column, get all text columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    goals.extend(df[col].dropna().astype(str).tolist())
        return goals
    
    def _extract_identity(self, df: pd.DataFrame) -> List[str]:
        """Extract identity markers from DataFrame"""
        identity = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['identity', 'self', 'personality', 'trait']):
                identity.extend(df[col].dropna().astype(str).tolist())
        return identity
    
    def _extract_experiences(self, df: pd.DataFrame) -> List[str]:
        """Extract experiences from DataFrame"""
        experiences = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['experience', 'lesson', 'learning', 'story']):
                experiences.extend(df[col].dropna().astype(str).tolist())
        return experiences
    
    def get_user_summary(self) -> str:
        """Generate a text summary of the user's data for LLM analysis
        
        Returns:
            Formatted text summary of user data
        """
        if not self.user_data:
            return "No user data available."
        
        summary_parts = []
        
        if self.user_data.get('values'):
            summary_parts.append(f"Values & Principles:\n{chr(10).join(['- ' + str(v) for v in self.user_data['values']])}")
        
        if self.user_data.get('goals'):
            summary_parts.append(f"Goals & Aspirations:\n{chr(10).join(['- ' + str(g) for g in self.user_data['goals']])}")
        
        if self.user_data.get('identity'):
            summary_parts.append(f"Identity & Personality:\n{chr(10).join(['- ' + str(i) for i in self.user_data['identity']])}")
        
        if self.user_data.get('experiences'):
            summary_parts.append(f"Experiences & Lessons:\n{chr(10).join(['- ' + str(e) for e in self.user_data['experiences']])}")
        
        if self.user_data.get('preferences'):
            pref_text = []
            for pref in self.user_data['preferences']:
                pref_text.append(f"From {pref['source']}:\n{pref['content']}")
            summary_parts.append(f"Additional Information:\n{chr(10).join(pref_text)}")
        
        return "\n\n".join(summary_parts) if summary_parts else "No structured data available." 