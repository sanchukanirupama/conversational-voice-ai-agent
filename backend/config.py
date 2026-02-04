import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # LangSmith / LangChain
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "Voice Agent Bank ABC")

    # App
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    GREETING_MESSAGE = os.getenv("GREETING_MESSAGE", "Welcome to Bank ABC. How can I help you?")
    CORS_ORIGINS = [s.strip() for s in os.getenv("CORS_ORIGINS", "*").split(",")]

    # LLM / Agent
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
    PROMPTS_FILE = os.getenv("PROMPTS_FILE", "backend/data/prompts.json")

    # Audio - STT
    STT_MODEL = os.getenv("STT_MODEL", "whisper-1")
    STT_LANGUAGE = os.getenv("STT_LANGUAGE", "en")
    STT_PROMPT = os.getenv("STT_PROMPT", "Bank ABC. Checking balance. Transfer money. Credit card. Account. Identity verification.")

    # Audio - TTS
    TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
    TTS_VOICE = os.getenv("TTS_VOICE", "alloy")
    AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", "4096"))

    # Data
    CUSTOMERS_FILE = os.getenv("CUSTOMERS_FILE", "backend/data/customers.json")
    DEFAULT_TRANSACTION_COUNT = int(os.getenv("DEFAULT_TRANSACTION_COUNT", "3"))

settings = Config()
