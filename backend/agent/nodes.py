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
        current_flow = state.get('active_flow', 'general')
        
        # Get last human message
        last_human = next(
            (m for m in reversed(messages) if isinstance(m, HumanMessage)), 
            None
        )
        if not last_human:
            return {"active_flow": current_flow}
        
        # Try keyword-based classification first (for high-confidence cases)
        keyword_flow = self._classify_by_keywords(last_human.content)
        if keyword_flow:
            print(f"[ROUTER DEBUG] Keyword match: '{last_human.content}' → {keyword_flow}")
            return {"active_flow": keyword_flow}
        
        # If already in a specific flow (not general), maintain it unless message indicates topic change
        if current_flow != 'general':
            # Check if message looks like a response to agent's question or continuation
            is_continuation = self._is_continuation(last_human.content)
            if is_continuation:
                print(f"[ROUTER DEBUG] Continuation detected, maintaining flow: {current_flow}")
                return {"active_flow": current_flow}
        
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
            print(f"[ROUTER DEBUG] LLM classification '{classification}' not in flows, defaulting to general")
            classification = "general"
        else:
            print(f"[ROUTER DEBUG] LLM classified: '{last_human.content}' → {classification}")
        
        return {"active_flow": classification}
    
    def _is_continuation(self, text: str) -> bool:
        """Check if text is a continuation response rather than new intent."""
        text_lower = text.lower().strip()
        
        # Short responses are likely continuations
        if len(text_lower.split()) <= 5:
            # Check for common continuation patterns
            continuation_patterns = [
                'yes', 'no', 'yeah', 'yep', 'nope', 'sure', 'ok', 'okay',
                'account', 'pin', 'number', 'password',
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',  # numbers
                'thank', 'please', 'help'
            ]
            if any(pattern in text_lower for pattern in continuation_patterns):
                return True
        
        # Check for account/PIN patterns
        if 'account' in text_lower or 'pin' in text_lower:
            return True
        
        # Check if it's mostly numbers (credentials)
        words = text_lower.split()
        number_words = [w for w in words if any(char.isdigit() for char in w)]
        if len(number_words) >= 2:  # Likely credentials
            return True
        
        return False
    
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
        # Use combination logic: action words + card identifiers
        card_actions = ['block', 'freeze', 'deactivate', 'cancel', 'lost', 'stolen', 'decline']
        card_identifiers = ['card', 'credit card', 'debit card', 'atm card']
        
        # Check if text contains any card action + any card identifier
        has_card_action = any(action in text_lower for action in card_actions)
        has_card_identifier = any(identifier in text_lower for identifier in card_identifiers)
        
        if has_card_action and has_card_identifier:
            return "card_atm_issues"
        
        # Also check for ATM-related issues
        if 'atm' in text_lower:
            atm_issues = ['problem', 'issue', 'not working', 'cash', 'dispens', 'stuck', 'retain']
            if any(issue in text_lower for issue in atm_issues):
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
        
        # Debug logging for tool calls
        if response.tool_calls:
            print(f"[DEBUG] Flow: {flow}, Verified: {is_verified}, Customer ID: {customer_id}")
            print(f"[DEBUG] Tool calls: {response.tool_calls}")
        
        # Check for termination
        is_call_over = self._check_termination(response)
        
        # Filter out premature t_end_call
        response = self._filter_premature_termination(response, state)
        
        return {"messages": [response], "is_call_over": is_call_over}
    
    def _build_system_message(self, flow: str, is_verified: bool, customer_id: str) -> str:
        """Build context-aware system prompt using unified configuration."""
        
        # Get flow-specific data
        flow_instructions_data = self.flow_config.get_flow_instructions(flow)
        conversation_strategy = self.flow_config.get_conversation_strategy(flow)
        
        # Automatically determine if this is a deep flow based on tools and instructions
        has_detailed_instructions = bool(
            flow_instructions_data.get("post_verification") or 
            flow_instructions_data.get("pre_verification")
        )
        
        # Base components
        workaround_instruction = (
            "\n\nIMPORTANT VERIFICATION NOTE: "
            "Can't hear 'Customer ID' well? Ask for 'Account Number' (4 digits) or 'Phone Number' instead. "
            "Prefer asking for Account Number and PIN for verification."
        )
        
        permission_note = ""
        if is_verified:
            # Get tools available for this flow
            flow_tools = self.flow_config.get_tools_for_flow(flow)
            tool_names = [t.name for t in flow_tools if t.name != 't_end_call']
            
            # Build comprehensive tool usage examples
            tool_examples = []
            if 't_get_balance' in tool_names:
                tool_examples.append(f"- Check balance: t_get_balance(customer_id='{customer_id}')")
            if 't_block_card' in tool_names:
                tool_examples.append(f"- Block card: t_block_card(customer_id='{customer_id}')")
            if 't_get_transactions' in tool_names:
                tool_examples.append(f"- Get transactions: t_get_transactions(customer_id='{customer_id}')")
            if 't_update_address' in tool_names:
                tool_examples.append(f"- Update address: t_update_address(customer_id='{customer_id}', new_address='...')")
            
            examples_str = "\n".join(tool_examples) if tool_examples else ""
            
            permission_note = (
                f"\n\n[SYSTEM UPDATE]: User is VERIFIED (Customer ID: {customer_id}). "
                "You have permission to disclose account details and perform actions.\n"
                f"\n🔑 CRITICAL: For ALL tool calls, you MUST use customer_id='{customer_id}'.\n"
                f"\n⚡ IMMEDIATE ACTION: When user confirms an action (says yes, sure, okay, please do it, etc.), "
                "you MUST IMMEDIATELY CALL THE TOOL. DO NOT just describe what will happen. "
                "For example, if user says 'yes block my card', you MUST call t_block_card(customer_id='{customer_id}') RIGHT NOW, "
                "not just say 'your card will be blocked'.\n"
                f"\nTool Usage Examples:\n{examples_str}\n"
                "\nProceed with the user's request immediately using these tools."
            )
            
            # Add strong tool usage enforcement
            if tool_names:
                permission_note += (
                    f"\n\n🔧 CRITICAL TOOL USAGE RULE: You have these tools available: {', '.join(tool_names)}. "
                    "If the user's request matches what any of these tools can do, you MUST use the tool. "
                    "DO NOT escalate to a human agent when you have the tool to solve it yourself. "
                    "For example, if user wants to block a card and you have t_block_card tool, USE IT IMMEDIATELY. "
                    "Only escalate if: (1) the tool fails technically, (2) user explicitly asks for human, or (3) you genuinely don't have a tool for the request."
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
        
        tool_execution_style = (
            "\n\n🎯 TOOL EXECUTION STYLE: When you need to use a tool, DO NOT announce it. "
            "Do NOT say 'please hold', 'let me check', 'I'll verify that', or similar phrases. "
            "Simply call the tool silently and report the RESULT. "
            "Example: Instead of 'Let me block your card...' → Just call t_block_card and say 'Your card has been blocked successfully.'"
        )
        
        # Build flow-specific instructions based on what's actually defined in config
        flow_specific_instructions = ""
        
        # If we have detailed instructions, use them
        if has_detailed_instructions:
            if is_verified:
                instructions_list = flow_instructions_data.get("post_verification", [])
                if instructions_list:
                    strategy_desc = conversation_strategy.get('description', '')
                    flow_specific_instructions = (
                        f"\n\n[FLOW: {flow.upper().replace('_', ' ')}]"
                        f"\n{strategy_desc}\n" if strategy_desc else "\n"
                        "\nYour instructions:"
                    )
                    for instruction in instructions_list[:20]:
                        flow_specific_instructions += f"\n- {instruction}"
                    
                    edge_cases = flow_instructions_data.get("edge_cases", [])
                    if edge_cases:
                        flow_specific_instructions += "\n\nEdge Cases:"
                        for case in edge_cases[:5]:
                            flow_specific_instructions += f"\n- {case}"
                    
                    flow_specific_instructions += f"\n\nYou have customer_id: {customer_id}"
            else:
                instructions_list = flow_instructions_data.get("pre_verification", [])
                if instructions_list:
                    flow_specific_instructions = (
                        f"\n\n[FLOW: {flow.upper().replace('_', ' ')} - VERIFICATION REQUIRED]"
                        "\n\nVerification steps:"
                    )
                    for instruction in instructions_list[:10]:
                        flow_specific_instructions += f"\n- {instruction}"
        
        # If we have interaction pattern (for escalation flows), use that
        elif flow_instructions_data.get("interaction_pattern"):
            interaction_pattern = flow_instructions_data.get("interaction_pattern", [])
            max_questions = self.flow_config.get_max_questions_before_escalation(flow)
            escalation_msg = self.flow_config.get_escalation_message(flow)
            strategy_desc = conversation_strategy.get('description', '')
            
            # Build VERY STRICT escalation instructions
            flow_specific_instructions = (
                f"\n\n[FLOW: {flow.upper().replace('_', ' ')} - ESCALATION REQUIRED]"
            )
            
            if strategy_desc:
                flow_specific_instructions += f"\n{strategy_desc}"
            
            if max_questions:
                flow_specific_instructions += (
                    f"\n\n🚨 HARD LIMIT: You may ask MAXIMUM {max_questions} question(s), then you MUST escalate."
                    f"\n🚨 STRICT PROHIBITION: Do NOT provide solutions, troubleshooting steps, or detailed instructions."
                    f"\n🚨 YOUR ONLY JOB: Gather basic context ({max_questions} question max), then transfer to specialist."
                )
            
            flow_specific_instructions += "\n\nYour exact approach:"
            
            for pattern in interaction_pattern:
                # Highlight STRICT RULES prominently
                if pattern.startswith("STRICT RULE") or pattern.startswith("IMMEDIATE"):
                    flow_specific_instructions += f"\n🚨 {pattern}"
                else:
                    flow_specific_instructions += f"\n- {pattern}"
            
            if escalation_msg:
                flow_specific_instructions += (
                    f"\n\n✅ After {max_questions or 2} question(s), you MUST say:"
                    f"\n\"{escalation_msg}\""
                )
        
        
        return f"{self.base_persona}\n\nCurrent Flow: {flow}\n{workaround_instruction}{strict_rule}{tool_execution_style}{termination_safety}{flow_specific_instructions}{permission_note}"

    
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
                    "verif" in text_content or      # catches verify, verified, verifying, verification
                    "check" in text_content or
                    "assist" in text_content or
                    "help" in text_content or
                    "being" in text_content or      # catches "is being verified"
                    "will" in text_content or       # catches "will help you"
                    "need" in text_content or       # catches "need to verify"
                    "provide" in text_content or    # catches "please provide"
                    "account" in text_content or    # catches "your account"
                    "identity" in text_content      # catches "verify identity"
                )
                
                if not other_tools_present and not is_continuation:
                    is_call_over = True
        
        return is_call_over
    
    def _filter_premature_termination(self, response, state: AgentState):
        """Remove t_end_call if inappropriate or other tools are present."""
        if not response.tool_calls:
            return response
        
        # Check if user actually expressed goodbye intent
        messages = state.get('messages', [])
        last_human = next(
            (m for m in reversed(messages) if isinstance(m, HumanMessage)),
            None
        )
        
        user_wants_to_end = False
        if last_human:
            last_text = last_human.content.lower()
            goodbye_phrases = ['bye', 'goodbye', 'thanks', 'thank you', "that's all", 'hang up', 'end call', 'no thanks']
            user_wants_to_end = any(phrase in last_text for phrase in goodbye_phrases)
        
        # If user didn't say goodbye, ALWAYS filter t_end_call
        if not user_wants_to_end:
            response.tool_calls = [
                tc for tc in response.tool_calls
                if tc['name'] != 't_end_call'
            ]
            return response
        
        # Original logic: Remove t_end_call if other tools are present
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
