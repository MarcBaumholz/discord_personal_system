#!/usr/bin/env python3
"""
Test script to verify the free Llama model works with OpenRouter API
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

def test_free_llama_model():
    """Test the free Llama model for text analysis"""
    
    print("🧪 Testing meta-llama/llama-4-maverick:free model...")
    
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
        response = client.chat.completions.create(
            model="meta-llama/llama-4-maverick:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content.strip()
        print("✅ SUCCESS! Free Llama model is working!")
        print(f"Response: {response_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_alternative_free_models():
    """Test alternative free models"""
    
    free_models_to_test = [
        "meta-llama/llama-4-maverick:free",
        "google/gemini-pro:free", 
        "anthropic/claude-3-haiku:beta",
        "deepseek/deepseek-chat-v3-0324:free"
    ]
    
    simple_prompt = """Respond with JSON: {"test": "working", "status": "ok"}"""
    
    working_models = []
    
    for model in free_models_to_test:
        print(f"\n🧪 Testing {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": simple_prompt}],
                max_tokens=50,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"✅ {model} - SUCCESS")
            working_models.append(model)
            
        except Exception as e:
            print(f"❌ {model} - FAILED: {str(e)[:100]}...")
    
    return working_models

if __name__ == "__main__":
    print("🔍 Testing Free Models for Money Bot...")
    
    # Test main Llama model
    llama_works = test_free_llama_model()
    
    # Test alternative free models
    print("\n" + "="*50)
    print("Testing alternative free models...")
    working_models = test_alternative_free_models()
    
    print(f"\n📊 Results:")
    print(f"Main Llama model working: {'✅' if llama_works else '❌'}")
    print(f"Working free models ({len(working_models)}): {working_models}")
    
    if working_models:
        print(f"\n✅ Great! You have {len(working_models)} working free models.")
        print("Your money bot should now work without costs!")
        print(f"Recommended model order: {working_models}")
    else:
        print("\n❌ No free models are working. Check your OpenRouter API key.")
