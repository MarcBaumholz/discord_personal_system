#!/usr/bin/env python3
"""
Test script for Home Assistant message processing
"""

import asyncio
import json
import re
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

async def test_home_assistant_message():
    """Test analyzing '5 euro essen' message from Marc Home Assistant"""
    
    test_text = "5 euro essen"
    author = "Marc Home Assistant"
    
    print(f"Testing text: '{test_text}'")
    print(f"Author: '{author}'")
    print("-" * 50)
    
    try:
        prompt = f"""
        Analyze this text for money/expense information:
        "{test_text}"
        
        Extract:
        1. Amount in euros (as a number)
        2. Category of expense (e.g., "Food", "Transport", "Shopping", "Bills", "Entertainment", etc.)
        3. Brief description
        
        Respond in JSON format:
        {{
            "amount": 12.50,
            "category": "Food",
            "description": "brief description of the expense"
        }}
        
        If no clear money amount is found, set amount to 0.
        """
        
        print("Sending request to AI...")
        response = await openai_client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
            timeout=10
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"AI Response: {response_text}")
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            result = {
                "amount": float(data.get("amount", 0)),
                "category": data.get("category", "Other"),
                "description": data.get("description", test_text[:100]),
                "author": author,
                "type": "text"
            }
            
            print("\n✅ ANALYSIS SUCCESSFUL:")
            print(f"Amount: €{result['amount']:.2f}")
            print(f"Category: {result['category']}")
            print(f"Description: {result['description']}")
            print(f"Author: {result['author']}")
            
            # Test person mapping
            author_lower = author.lower()
            if 'marc' in author_lower or 'baumholz' in author_lower:
                person = 'Marc'
            else:
                person = 'Marc'  # Default
            
            print(f"Person: {person}")
            
            return result
        else:
            print("❌ No JSON found in response")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def test_alternative_models():
    """Test with alternative models in case DeepSeek has rate limits"""
    
    test_text = "5 euro essen"
    
    # Alternative free models to try
    models = [
        "anthropic/claude-3-haiku:free",
        "google/gemini-flash-1.5:free",
        "mistralai/mistral-7b-instruct:free"
    ]
    
    for model in models:
        print(f"\n🔄 Testing model: {model}")
        try:
            prompt = f"""
            Analyze this German text for money information: "{test_text}"
            
            Return JSON with amount (number), category (Food/Transport/etc), description.
            Example: {{"amount": 5.0, "category": "Food", "description": "food expense"}}
            """
            
            response = await openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
                timeout=8
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"✅ {model}: {response_text}")
            
        except Exception as e:
            print(f"❌ {model}: {e}")

if __name__ == "__main__":
    print("🧪 Testing Home Assistant Message Processing")
    print("=" * 60)
    
    # Test main analysis
    result = asyncio.run(test_home_assistant_message())
    
    if not result or result.get('amount', 0) == 0:
        print("\n🔄 Testing alternative models...")
        asyncio.run(test_alternative_models())
