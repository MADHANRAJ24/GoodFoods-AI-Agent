import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# We default to Groq if GROQ_API_KEY is present, otherwise try OpenAI
API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else None
MODEL = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile" if os.getenv("GROQ_API_KEY") else "gpt-3.5-turbo")

if not API_KEY:
    raise ValueError("Missing API Key. Please set GROQ_API_KEY or OPENAI_API_KEY in your environment.")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

def get_chat_completion(messages, tools=None):
    """Provides a unified interface to get a chat completion from the configured LLM."""
    params = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.3 # Keep temperature low for reliable tool calling
    }
    if tools:
        params["tools"] = tools
        params["tool_choice"] = "auto"
        
    return client.chat.completions.create(**params)
