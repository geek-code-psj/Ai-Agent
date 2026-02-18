
import sys
import os
import traceback
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
    sys.exit(1)

print(f"API Key: {api_key[:10]}...")

genai.configure(api_key=api_key)

models_to_try = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro", "gemini-1.5-pro"]

for model_name in models_to_try:
    print(f"\n--- Testing Model: {model_name} ---")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello")
        print(f"SUCCESS: {model_name}")
        print(f"Response: {response.text}")
        break
    except Exception as e:
        print(f"FAILED: {model_name} - Error: {e}")
