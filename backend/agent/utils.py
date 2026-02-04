"""
Utility Functions

Helper functions for the agent, including contextual response generation.
"""

from typing import List, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from backend.config import settings


async def generate_contextual_response(
    messages: List[BaseMessage], 
    type: Literal["nudge", "closing_silence", "closing_goodbye", "pardon"]
) -> str:
    """
    Generates context-aware system messages for idle timeouts and errors.
    
    Used by WebSocket handler to:
    - Send nudges when user is silent
    - Generate polite goodbyes
    - Handle unintelligible audio
    
    Args:
        messages: Recent conversation history
        type: Type of message to generate
    
    Returns:
        Generated message string
    """
    llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.7)
    
    prompts = {
        "nudge": (
            "The user has been silent for a while. "
            "Generate a short, polite, 1-sentence nudge asking if they are still there or if they need more time. "
            "Do NOT repeat the last assistant message. Keep it natural."
        ),
        "closing_silence": (
            "The user has been silent for too long. "
            "Generate a polite 1-sentence closing message to end the call (e.g., 'I didn't hear a response, so I will end the call')."
        ),
        "closing_goodbye": (
            "The call is ending. Generate a warm, polite 1-sentence goodbye message (e.g. 'Thank you for calling Bank ABC, have a great day.')."
        ),
        "pardon": (
            "The user said something but it was unintelligible or empty. "
            "Generate a polite 1-sentence request for them to repeat themselves (e.g. 'I'm sorry, I didn't catch that. Could you say it again?')."
        )
    }
    
    prompt = prompts.get(type, "Are you still there?")
    
    # Sanitize history (strip tool_calls to avoid API errors)
    recent_messages = []
    for m in messages[-10:]:
        if isinstance(m, HumanMessage):
            recent_messages.append(m)
        elif isinstance(m, AIMessage) and m.content:
            recent_messages.append(AIMessage(content=str(m.content)))
    
    recent_history = recent_messages[-4:]
    
    try:
        response = await llm.ainvoke([SystemMessage(content=prompt)] + recent_history)
        return response.content.strip() or "Are you still there?"
    except Exception as e:
        print(f"Error generating system message: {e}")
        # Fallbacks
        fallbacks = {
            "nudge": "Are you still there?",
            "closing_silence": "I am not hearing any response. Goodbye.",
            "closing_goodbye": "Thank you for calling. Goodbye."
        }
        return fallbacks.get(type, "Are you still there?")
