#!/usr/bin/env python3
"""
Test script to verify vision models work with OpenRouter API
"""
import os
import sys
import base64
import requests
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
    
    # Create a simple test image (base64 encoded red square)
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    models_to_test = [
        "openai/gpt-4-vision-preview",
        "openai/gpt-4o",
        "anthropic/claude-3-haiku:beta",
        "anthropic/claude-3-sonnet:beta",
        "google/gemini-pro-vision",
        "google/gemini-1.5-flash-latest"
    ]
    
    prompt = """What do you see in this image? Respond in JSON format:
    {
        "description": "what you see",
        "colors": ["list of colors"],
        "objects": ["list of objects"]
    }"""
    
    working_models = []
    
    for model in models_to_test:
        print(f"\n🧪 Testing model: {model}")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
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
            
            response_text = response.choices[0].message.content.strip()
            print(f"✅ {model} - SUCCESS")
            print(f"   Response: {response_text[:100]}...")
            working_models.append(model)
            
        except Exception as e:
            print(f"❌ {model} - FAILED: {str(e)[:100]}...")
    
    print(f"\n📊 Results:")
    print(f"Working models ({len(working_models)}): {working_models}")
    print(f"Failed models: {len(models_to_test) - len(working_models)}")
    
    return working_models

if __name__ == "__main__":
    print("🔍 Testing OpenRouter Vision Models...")
    working_models = test_vision_models()
    
    if working_models:
        print(f"\n✅ Great! You have {len(working_models)} working vision models.")
        print("Your money bot should now work with image analysis!")
    else:
        print("\n❌ No vision models are working. Check your OpenRouter API key and subscription.")
