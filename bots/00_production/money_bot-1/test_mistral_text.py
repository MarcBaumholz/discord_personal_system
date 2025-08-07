#!/usr/bin/env python3
"""
Test script to check if Mistral model works for text-only analysis
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(env_path)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found!")
    sys.exit(1)

# Initialize OpenAI client for OpenRouter
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

def test_mistral_text():
    """Test Mistral model for text analysis only"""
    
    print("🧪 Testing mistralai/mistral-small-3.2-24b-instruct:free for text analysis...")
    
    prompt = """
    Analyze this text for money/expense information:
    "Bought groceries at Rewe for 25.50 euros"
    
    Extract:
    1. Amount in euros (as a number)
    2. Category of expense (e.g., "Food", "Transport", "Shopping", "Bills", "Entertainment", etc.)
    3. Brief description
    
    Respond in JSON format:
    {
        "amount": 12.50,
        "category": "Food",
        "description": "brief description of the expense"
    }
    
    If no clear money amount is found, set amount to 0.
    """
    
    try:
        print("Making text API call...")
        response = client.chat.completions.create(
            model="mistralai/mistral-small-3.2-24b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        
        print(f"Raw response: {response}")
        
        if response and response.choices and len(response.choices) > 0:
            response_text = response.choices[0].message.content.strip()
            print("✅ SUCCESS! Mistral text model is working!")
            print(f"Response: {response_text}")
            return True
        else:
            print("❌ Empty response from model")
            return False
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Mistral Text Model...")
    
    mistral_works = test_mistral_text()
    
    if mistral_works:
        print("\n✅ Great! The Mistral text model is working!")
        print("Will use this for text analysis and fallback for images.")
    else:
        print("\n❌ Mistral model failed completely.")
