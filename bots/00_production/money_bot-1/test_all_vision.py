#!/usr/bin/env python3
"""
Test script to find working free vision models
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

def test_vision_models():
    """Test different vision models to see which ones work"""
    
    # Create a simple test image
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA60e6kgAAAABJRU5ErkJggg=="
    
    vision_models_to_test = [
        "moonshotai/kimi-vl-a3b-thinking:free",
        "google/gemini-flash-1.5:free", 
        "anthropic/claude-3-haiku:beta",
        "openai/gpt-4o-mini:free",
        "meta-llama/llama-3.2-11b-vision:free",
        "qwen/qwen-2-vl-7b:free"
    ]
    
    simple_prompt = """Look at this image and respond with JSON: {"test": "working", "can_see_image": true}"""
    
    working_models = []
    
    for model in vision_models_to_test:
        print(f"\n🧪 Testing {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": simple_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{test_image_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            if response and response.choices and len(response.choices) > 0:
                response_text = response.choices[0].message.content.strip()
                print(f"✅ {model} - SUCCESS")
                print(f"   Response: {response_text[:100]}...")
                working_models.append(model)
            else:
                print(f"❌ {model} - Empty response")
                
        except Exception as e:
            print(f"❌ {model} - FAILED: {str(e)[:100]}...")
    
    return working_models

if __name__ == "__main__":
    print("🔍 Testing Free Vision Models...")
    
    working_models = test_vision_models()
    
    print(f"\n📊 Results:")
    print(f"Working vision models ({len(working_models)}): {working_models}")
    
    if working_models:
        print(f"\n✅ Great! You have {len(working_models)} working vision models.")
        print("Will update the bot to use the best working model!")
    else:
        print("\n❌ No vision models are working. Will use text-only fallback.")
