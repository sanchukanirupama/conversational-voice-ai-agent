"""
Graph Nodes

Implements the three main node types: Router, Gate, and Executor.
Each node is a class that processes state and returns updates.
"""

import re
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from backend.config import settings
from backend.tools import get_customer_by_id
from backend.agent.state import AgentState
from backend.agent.config import FlowConfig


class RouterNode:
    """
    Classifies user intent into one of the predefined flows.
    
    Uses keyword-based pre-classification for high-confidence cases,
    then falls back to LLM for ambiguous intents.
    Tagged with 'router_classification' for LangSmith tracing.
    """
    
    def __init__(self, flow_config: FlowConfig):
        self.flow_config = flow_config
        self._llm = None
    
    @property
    def llm(self):
        """Lazy initialization of LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0)
        return self._llm
    
    def __call__(self, state: AgentState) -> Dict:
        """
        Process state and classify intent.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dictionary with updated active_flow
        """
        messages = state['messages']
        
        # Get last human message
        last_human = next(
            (m for m in reversed(messages) if isinstance(m, HumanMessage)), 
            None
        )
        if not last_human:
            return {"active_flow": "general"}
        
        # Try keyword-based classification first (for high-confidence cases)
        keyword_flow = self._classify_by_keywords(last_human.content)
        if keyword_flow:
            return {"active_flow": keyword_flow}
        
        # Get recent context (last 5 messages or fewer)
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        context_messages = [m for m in recent_messages if isinstance(m, HumanMessage)]
        
        # Build prompt and classify using LLM
        system_prompt = self.flow_config.build_router_prompt()
        
        # Use last human message + context hint if available
        context_hint = ""
        if len(context_messages) > 1:
            context_hint = f"\n[Recent context: User previously mentioned topics related to their inquiry]"
        
        classification = self.llm.invoke(
            [SystemMessage(content=system_prompt + context_hint), last_human],
            config={"tags": ["router_classification"]}
        ).content.strip().lower()
        
        # Sanitize
        if classification not in self.flow_config.flow_tools.keys():
            classification = "general"
        
        return {"active_flow": classification}
    
    def _classify_by_keywords(self, text: str) -> str | None:
        """
        Pre-classify based on strict keywords for high-confidence cases.
        
        Args:
            text: User message text
            
        Returns:
            Flow name if keywords match, None otherwise
        """
        text_lower = text.lower()
        
        # High-priority card/ATM keywords (security-sensitive)
        card_keywords = [
            "block card", "freeze card", "lost card", "stolen card",
            "block my card", "freeze my card", "lost my card", "stolen my card",
            "card was stolen", "card is lost", "deactivate card",
            "card declined", "card not working", "atm"
        ]
        
        for keyword in card_keywords:
            if keyword in text_lower:
                return "card_atm_issues"
        
        return None


class VerificationGate:
    """
    Security checkpoint for sensitive flows.
    
    Responsibilities:
    - Checks if current flow requires verification
    - Detects successful verification from tool results
    - Injects verification prompts when needed
    """
    
    def __init__(self, flow_config: FlowConfig):
        self.flow_config = flow_config
    
    def __call__(self, state: AgentState) -> Dict:
        """
        Process state and manage verification.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dictionary with verification updates or prompts
        """
        flow = state.get('active_flow', 'general')
        is_verified = state.get('is_verified', False)
        messages = state['messages']
        
        # Check if we just verified (last message is ToolMessage with success)
        if len(messages) > 0 and isinstance(messages[-1], ToolMessage):
            content = messages[-1].content
            if "Identity Verified successfully" in content:
                # Extract customer_id from tool result
                match = re.search(r"Customer ID: (\w+)", content)
                customer_id = match.group(1) if match else None
                return {"is_verified": True, "customer_id": customer_id}
        
        # If flow requires verification and not yet verified, inject prompt
        if self.flow_config.is_sensitive_flow(flow) and not is_verified:
            return {
                "messages": [
                    SystemMessage(
                        content="Current Flow requires VERIFICATION. You MUST ask for Account Number and PIN if not provided. Do not perform the action until verified."
                    )
                ]
            }
        
        return {}


class FlowExecutor:
    """
    Main conversation executor with tool binding.
    
    Responsibilities:
    - Selects tools based on active flow
    - Builds context-aware system prompts
    - Invokes LLM with tools
    - Handles termination logic
    
    Tagged with 'flow:<active_flow>' for LangSmith tracing.
    """
    
    def __init__(self, flow_config: FlowConfig):
        self.flow_config = flow_config
        self.base_persona = settings.PROMPTS.get(
            "system_persona", 
            "You are a banking assistant."
        )
    
    def __call__(self, state: AgentState) -> Dict:
        """
        Execute conversation turn with tools.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dictionary with AI response and termination flag
        """
        flow = state.get('active_flow', 'general')
        messages = state['messages']
        is_verified = state.get('is_verified', False)
        customer_id = state.get('customer_id', "Unknown")
        
        # Get tools and bind to LLM
        flow_tools = self.flow_config.get_tools_for_flow(flow)
        llm = ChatOpenAI(
            model=settings.LLM_MODEL, 
            temperature=settings.LLM_TEMPERATURE
        ).bind_tools(flow_tools)
        
        # Build system prompt
        sys_msg = self._build_system_message(flow, is_verified, customer_id)
        
        # Invoke LLM with tracing
        response = llm.invoke(
            [SystemMessage(content=sys_msg)] + messages,
            config={
                "tags": [f"flow:{flow}"],
                "metadata": {
                    "customer_id": customer_id,
                    "is_verified": is_verified,
                    "active_flow": flow
                }
            }
        )
        
        # Check for termination
        is_call_over = self._check_termination(response)
        
        # Filter out premature t_end_call
        response = self._filter_premature_termination(response)
        
        return {"messages": [response], "is_call_over": is_call_over}
    
    def _build_system_message(self, flow: str, is_verified: bool, customer_id: str) -> str:
        """Build context-aware system prompt."""
        workaround_instruction = (
            "\n\nIMPORTANT VERIFICATION NOTE: "
            "Can't hear 'Customer ID' well? Ask for 'Account Number' (4 digits) or 'Phone Number' instead. "
            "Prefer asking for Account Number and PIN for verification."
        )
        
        permission_note = ""
        if is_verified:
            permission_note = (
                f"\n\n[SYSTEM UPDATE]: User is VERIFIED (Customer ID: {customer_id}). "
                "You have permission to disclose account details and perform actions. "
                f"To check balance, call tool: t_get_balance(customer_id='{customer_id}'). "
                "Proceed with the user's request immediately."
            )
        
        strict_rule = (
            "\n\nCRITICAL DATA RULE: You DO NOT know any account details (balance, transactions) "
            "unless you use the provided tools. DO NOT hallucinate or guess numbers. "
            "Always call the tool to get the latest data."
        )
        
        termination_safety = (
            "\n\nTERMINATION RULE: NEVER call t_end_call to finish a task. "
            "Only call t_end_call when the USER explicitly says goodbye or asks to end the call. "
            "If you have completed a task (like verification), ask the user what else they need."
        )
        
        # Flow-specific strict instructions
        flow_instructions = ""
        if flow == "card_atm_issues":
            flow_instructions = (
                "\n\n[FLOW: CARD/ATM ISSUES - STRICT MODE]"
                "\nYou are handling CARD AND ATM PROBLEMS ONLY."
                "\n- Focus on: card blocking, lost/stolen cards, ATM issues, card decline"
                "\n- Do NOT handle: balance inquiries, transaction history (redirect to account servicing)"
                "\n- When user wants to block card after verification: Call t_block_card immediately"
                f"\n- You have customer_id: {customer_id if is_verified else 'PENDING VERIFICATION'}"
                "\n- Tool usage: t_block_card(customer_id='{customer_id}') - NO need for card_id, system finds it automatically"
                if is_verified else
                "\n\n[FLOW: CARD/ATM ISSUES - VERIFICATION REQUIRED]"
                "\nUser is reporting a card/ATM problem. This is URGENT for security."
                "\nYou MUST verify identity first before blocking card."
                "\nAsk for Account Number and PIN to proceed."
            )
        elif flow == "account_servicing":
            flow_instructions = (
                "\n\n[FLOW: ACCOUNT SERVICING - STRICT MODE]"
                "\nYou are handling ACCOUNT INFORMATION ONLY."
                "\n- Focus on: balance, transactions, statements, profile updates"
                "\n- Do NOT handle: card blocking, ATM issues, lost/stolen cards"
                "\n- If user mentions card blocking, inform them you'll need to switch to card services"
            )
        
        return f"{self.base_persona}\n\nCurrent Flow: {flow}\n{workaround_instruction}{strict_rule}{termination_safety}{flow_instructions}{permission_note}"
    
    def _check_termination(self, response) -> bool:
        """Check if call should end based on tool calls."""
        is_call_over = False
        
        if not response.tool_calls:
            return False
        
        # Check if other tools are present besides t_end_call
        other_tools_present = any(
            tc['name'] != 't_end_call' 
            for tc in response.tool_calls
        )
        
        for tc in response.tool_calls:
            if tc['name'] == 't_end_call':
                # Heuristic: If agent text suggests continuation, ignore end_call
                text_content = str(response.content).lower()
                is_continuation = (
                    "check" in text_content or 
                    "verify" in text_content or 
                    "assist" in text_content
                )
                
                if not other_tools_present and not is_continuation:
                    is_call_over = True
        
        return is_call_over
    
    def _filter_premature_termination(self, response):
        """Remove t_end_call if other tools are present."""
        if not response.tool_calls:
            return response
        
        other_tools_present = any(
            tc['name'] != 't_end_call' 
            for tc in response.tool_calls
        )
        
        if other_tools_present:
            response.tool_calls = [
                tc for tc in response.tool_calls 
                if tc['name'] != 't_end_call'
            ]
        
        return response
