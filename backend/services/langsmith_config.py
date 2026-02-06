"""
LangSmith Configuration Module

Initializes the centralized LangSmith tracer service.
"""

from backend.services.langsmith_tracer import tracer


def init_langsmith():
    """
    Initializes LangSmith tracing if configured.

    Uses the centralized tracer service for consistent configuration.
    """
    tracer.initialize()
