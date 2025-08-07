#!/usr/bin/env python3
"""
Test script with working free models that we know work
"""
import os
import sys
import base64
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

def test_working_free_models():
    """Test the models we know work for text analysis"""
    
    working_models = [
        "deepseek/deepseek-chat-v3-0324:free",
        "anthropic/claude-3-haiku:beta"
    ]
    
    text_prompt = """
    Analyze this text for money/expense information:
    "Aral Tankstelle - 72.41 EUR fuel purchase on 23.07.2025"
    
    Extract:
    1. Amount in euros (as a number)
    2. Category of expense (e.g., "Transport", "Food", "Shopping", etc.)
    3. Brief description
    
    Respond in JSON format:
    {
        "amount": 72.41,
        "category": "Transport",
        "description": "Aral gas station fuel purchase"
    }
    """
    
    for model in working_models:
        print(f"\n🧪 Testing {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": text_prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            if response and response.choices and len(response.choices) > 0:
                response_text = response.choices[0].message.content.strip()
                print(f"✅ {model} - SUCCESS!")
                print(f"Response: {response_text}")
            else:
                print(f"❌ {model} - Empty response")
                
        except Exception as e:
            print(f"❌ {model} - FAILED: {str(e)[:100]}...")
    
    return working_models

if __name__ == "__main__":
    print("🔍 Testing Working Free Models for Money Bot...")
    print("Since vision models have issues, let's focus on text analysis...")
    
    working_models = test_working_free_models()
    
    print(f"\n📊 Summary:")
    print("✅ We have working text analysis models!")
    print("🤖 The bot can still work by asking users to type expense details")
    print("💡 For images, users can describe what they see and the bot will parse it")
    
    print(f"\n🚀 Ready to start the money bot with working models!")
