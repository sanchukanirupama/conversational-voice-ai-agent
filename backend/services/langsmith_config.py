import os
from backend.config import settings

def init_langsmith():
    """ Initializes LangSmith tracing if configured. """
    if settings.LANGCHAIN_TRACING_V2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        print(f"LangSmith Tracing Enabled: {settings.LANGCHAIN_PROJECT}")
    else:
        print("LangSmith Tracing Disabled")
