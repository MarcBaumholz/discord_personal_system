import os
import logging
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('routine_bot.openrouter_service')

class OpenRouterService:
    """Service to interact with OpenRouter LLM API for routine formatting and suggestions"""
    
    def __init__(self):
        """Initialize OpenRouter service"""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        logger.info("Initializing OpenRouter Service")
    
    def generate_structured_routine_steps(self, routine):
        """
        Generate structured, clear steps for a routine using DeepSeek
        
        Args:
            routine: Routine object with notes field containing raw steps
            
        Returns:
            list: List of structured, clear steps
        """
        try:
            notes = routine.get('notes', '')
            routine_name = routine.get('name', 'Routine')
            time_of_day = routine.get('time_of_day')
            
            # Handle None time_of_day
            time_of_day_str = time_of_day.lower() if time_of_day else 'daily'
            
            # If no notes, try to generate steps for common routines
            if not notes:
                logger.info(f"No notes found for routine '{routine_name}', generating default steps")
                
            # Prepare the prompt for DeepSeek
            prompt = f"""I need you to create a clear, structured list of steps for my {time_of_day_str} routine named "{routine_name}".

Here are the raw notes I have for this routine (if empty, please create sensible default steps for this type of routine):
{notes}

Please:
1. Create a numbered list of clear, actionable steps
2. Each step should be concise (max 10 words per step)
3. Break complex steps into simpler sub-steps
4. Ensure steps are in logical order
5. Return ONLY the numbered list of steps, one per line
6. Use 5-10 steps total

Format example:
1. Drink a glass of water
2. Stretch for 5 minutes
3. Meditate for 10 minutes

The steps should be practical, clear, and easy to check off as completed.
"""

            # Call DeepSeek via OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek/deepseek-chat-v3-0324:free",  # Specifically using DeepSeek
                "messages": [
                    {"role": "system", "content": "You are a routine planning assistant. Create clear, structured steps for routines."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.3  # Lower temperature for more consistent output
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    steps_text = result['choices'][0]['message']['content']
                    
                    # Process the returned text into a list of steps
                    steps = []
                    for line in steps_text.split('\n'):
                        # Remove numbers, periods, and leading/trailing whitespace
                        line = line.strip()
                        if line and not line.isspace():
                            # Remove leading numbers (e.g., "1. ", "1)", etc.)
                            import re
                            clean_line = re.sub(r'^\d+[\.\)\-]\s*', '', line)
                            if clean_line:
                                steps.append(clean_line.strip())
                    
                    logger.info(f"Generated {len(steps)} structured steps for routine: {routine_name}")
                    return steps
            
            logger.error(f"Error from DeepSeek API: {response.status_code} - {response.text}")
            return self._parse_fallback_steps(notes)
            
        except Exception as e:
            logger.error(f"Error generating structured steps: {e}")
            return self._parse_fallback_steps(notes)
    
    def _parse_fallback_steps(self, notes):
        """Parse routine notes into steps as a fallback if API fails"""
        if not notes:
            return ["Complete routine task"]
            
        steps = []
        for line in notes.split('\n'):
            line = line.strip()
            if line and not line.isspace():
                # Remove leading numbers, bullets, etc.
                import re
                clean_line = re.sub(r'^[\d\.\-\*\•\⁃\◦\○\▪\■\□\▫\❏\❑\❒\➤\➣\➢\➡\→\►\➔\✓\✔\✗\✘\☐\☑\☒]+\s*', '', line)
                if clean_line:
                    steps.append(clean_line.strip())
        
        if not steps:
            steps = ["Complete routine task"]
            
        return steps
    
    def format_routine_message(self, routines, day_part=None, date=None):
        """
        Generate a formatted routine message using OpenRouter
        
        Args:
            routines: List of routine objects from Notion
            day_part: Part of day (Morning, Afternoon, Evening, or None for all)
            date: Date for the routines (defaults to today)
            
        Returns:
            str: Formatted routine message
        """
        if not routines:
            return f"No routines scheduled for {day_part.lower() if day_part else 'today'}."
        
        try:
            # Format date as a readable string
            if date:
                date_str = date.strftime("%A, %B %d, %Y")
            else:
                date_str = datetime.now().strftime("%A, %B %d, %Y")
            
            # Prepare routines data for the LLM
            routine_data = []
            for routine in routines:
                routine_data.append({
                    "name": routine.get('name', 'Unnamed Routine'),
                    "time_of_day": routine.get('time_of_day', 'Anytime'),
                    "duration": routine.get('duration', 0),
                    "status": routine.get('status', 'Not Started')
                })
            
            # Create the prompt based on the time of day
            if day_part:
                prompt = f"""Create a clear, motivating message for my {day_part.lower()} routine on {date_str}. 
Here are my scheduled routines:

{json.dumps(routine_data, indent=2)}

Format the message with:
1. A brief motivational introduction
2. A clear, organized list of my routines with their durations
3. A helpful tip related to the activities

Keep it concise (max 250 words) but friendly and motivating. Use emojis where appropriate."""
            else:
                prompt = f"""Create a clear, organized message outlining my daily routine plan for {date_str}.
Here are my scheduled routines:

{json.dumps(routine_data, indent=2)}

Format the message with:
1. A brief introduction for the day
2. Routines organized by time of day (Morning, Afternoon, Evening)
3. Duration estimates for each routine
4. A motivational closing note

Make it concise (max 350 words) but friendly and engaging. Use emojis where appropriate."""

            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek/deepseek-chat-v3-0324:free",  # Using a reliable model that's low cost
                "messages": [
                    {"role": "system", "content": "You are a helpful routine assistant that creates clear, motivating schedules."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
            
            logger.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
            return self._create_fallback_routine_message(routines, day_part, date_str)
            
        except Exception as e:
            logger.error(f"Error formatting routine message: {e}")
            return self._create_fallback_routine_message(routines, day_part, date)
    
    def _create_fallback_routine_message(self, routines, day_part=None, date_str=None):
        """Create a basic formatted message when the API fails"""
        if not date_str:
            date_str = datetime.now().strftime("%A, %B %d, %Y")
            
        if day_part:
            message = f"## {day_part} Routines for {date_str}\n\n"
        else:
            message = f"## Daily Routines for {date_str}\n\n"
        
        # Group routines by time of day if no specific day part
        if not day_part:
            routines_by_time = {}
            for routine in routines:
                time = routine.get('time_of_day', 'Other')
                if time not in routines_by_time:
                    routines_by_time[time] = []
                routines_by_time[time].append(routine)
            
            # Standard times to ensure proper order
            standard_times = ['Morning', 'Afternoon', 'Evening']
            
            for time in standard_times:
                if time in routines_by_time and routines_by_time[time]:
                    message += f"### {time}\n\n"
                    for routine in routines_by_time[time]:
                        duration = f" ({routine.get('duration', 0)} min)" if routine.get('duration') else ""
                        message += f"- {routine.get('name', 'Unnamed Routine')}{duration}\n"
                    message += "\n"
        else:
            # Just list all routines for the specified time
            for routine in routines:
                duration = f" ({routine.get('duration', 0)} min)" if routine.get('duration') else ""
                message += f"- {routine.get('name', 'Unnamed Routine')}{duration}\n"
        
        message += "\nHave a productive day!"
        return message 