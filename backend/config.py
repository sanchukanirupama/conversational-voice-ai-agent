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
    PROMPTS_FILE = os.getenv("PROMPTS_FILE", "backend/data/unified_configuration.json")

    # Audio - STT
    STT_MODEL = os.getenv("STT_MODEL", "whisper-1")
    STT_LANGUAGE = os.getenv("STT_LANGUAGE", "en")
    STT_PROMPT = os.getenv("STT_PROMPT", "Bank ABC. Customer ID. PIN number. OTP code. ATM. beneficiary. card declined. disputed transaction.")

    # Audio - TTS
    TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
    TTS_VOICE = os.getenv("TTS_VOICE", "alloy")
    AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", "4096"))

    # Data
    CUSTOMERS_FILE = os.getenv("CUSTOMERS_FILE", "backend/data/customers.json")
    DEFAULT_TRANSACTION_COUNT = int(os.getenv("DEFAULT_TRANSACTION_COUNT", "3"))

    # Admin Authentication
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    def load_prompts(self):
        """
        Load unified configuration with all prompts, flows, tools, and strategies.
        Provides backward-compatible access to prompts while adding new sections.
        """
        import json
        try:
            with open(self.PROMPTS_FILE, 'r') as f:
                config = json.load(f)
                
                # For backward compatibility, return the full config
                # Code can access: settings.PROMPTS["system_persona"], etc.
                return config
        except FileNotFoundError:
            print(f"Configuration file not found: {self.PROMPTS_FILE}")
            print("Falling back to minimal default configuration")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration JSON: {e}")
            return self._get_default_config()
        except Exception as e:
            print(f"Unexpected error loading configuration: {e}")
            return self._get_default_config()
    
    def reload_prompts(self):
        """Reload the prompts configuration from file (for dynamic updates)"""
        self.PROMPTS = self.load_prompts()
    
    def _get_default_config(self):
        """Fallback configuration if file loading fails"""
        return {
            "system_persona": "You are a banking assistant.",
            "greeting": "Welcome to Bank ABC. How can I help you?",
            "routing_flows": {},
            "tool_registry": {},
            "escalation_strategies": {}
        }

settings = Config()
settings.PROMPTS = settings.load_prompts()
