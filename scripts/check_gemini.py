import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API key found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("Available Models supporting generateContent:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f" - {m.name}")
