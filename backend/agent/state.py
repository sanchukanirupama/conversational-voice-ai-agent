"""
Agent State Schema

Defines the conversation state structure tracked across all graph nodes.
"""

from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Conversation State tracked across all nodes.

    Fields:
        messages: Full conversation history (Human + AI + Tool messages)
        customer_id: Extracted after successful verification
        account_number: Optional context for verification
        is_verified: Whether identity check passed
        is_call_over: Flag to terminate the call
        active_flow: Current routing category (e.g., 'account_servicing')
        call_id: Unique identifier for this conversation session (for tracing)
    """
    messages: Annotated[List[BaseMessage], add_messages]
    customer_id: str | None
    account_number: str | None
    is_verified: bool
    is_call_over: bool
    active_flow: str
    call_id: str | None
