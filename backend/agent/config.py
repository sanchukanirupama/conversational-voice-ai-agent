"""
Flow Configuration

Manages flow definitions, tool mappings, and sensitive flow detection.
"""

from typing import Dict, List
from backend.config import settings
from backend.agent.tools_registry import TOOL_REGISTRY, t_verify_identity, t_end_call


class FlowConfig:
    """
    Manages flow configurations loaded from unified_configuration.json.
    
    Responsibilities:
    - Load and parse flow definitions
    - Map tool names to tool objects
    - Identify flows requiring verification
    - Provide access to flow instructions and conversation strategies
    - Manage escalation logic and verification prompts
    """
    
    def __init__(self):
        self.config = settings.PROMPTS
        self.routing_flows = self.config.get("routing_flows", {})
        self.flow_tools = self._build_flow_tools()
        self.sensitive_flows = self._build_sensitive_flows()
        self.verification_prompts = self.config.get("verification_prompts", {})
        self.escalation_strategies = self.config.get("escalation_strategies", {})
    
    def _build_flow_tools(self) -> Dict[str, List]:
        """
        Builds a mapping of flow_name -> [tool_objects].
        
        Returns:
            Dictionary mapping flow names to lists of tool objects
        """
        flow_tools = {}
        
        for flow_key, flow_data in self.routing_flows.items():
            tool_names = flow_data.get("tools", [])
            mapped_tools = [
                TOOL_REGISTRY[name] 
                for name in tool_names 
                if name in TOOL_REGISTRY
            ]
            flow_tools[flow_key] = mapped_tools
        
        # Add 'general' flow fallback
        if "general" not in flow_tools:
            flow_tools["general"] = [t_verify_identity]
        
        return flow_tools
    
    def _build_sensitive_flows(self) -> List[str]:
        """
        Identifies flows that require identity verification.
        
        Returns:
            List of flow names requiring verification
        """
        return [
            key for key, data in self.routing_flows.items() 
            if data.get("requires_verification", False)
        ]
    
    def get_tools_for_flow(self, flow_name: str) -> List:
        """
        Get tools for a specific flow, always including t_end_call.
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            List of tool objects for this flow
        """
        tools = self.flow_tools.get(flow_name, self.flow_tools['general']).copy()
        if t_end_call not in tools:
            tools.append(t_end_call)
        return tools
    
    def is_sensitive_flow(self, flow_name: str) -> bool:
        """
        Check if a flow requires verification.
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            True if verification is required
        """
        return flow_name in self.sensitive_flows
    
    def build_router_prompt(self) -> str:
        """
        Dynamically builds the router classification prompt with strict rules and examples.
        
        Returns:
            System prompt string for the router
        """
        prompt_lines = [
            "You are a banking router. Classify the user's intent into EXACTLY ONE category.",
            "",
            "=== STRICT CLASSIFICATION RULES ===",
            "1. CARD/ATM keywords (block, freeze, lost, stolen, ATM, card declined) → card_atm_issues",
            "2. ACCOUNT INFO keywords (balance, transactions, statement) → account_servicing",
            "3. If BOTH mentioned, prioritize CARD SAFETY → card_atm_issues",
            "4. Greeting/unclear → general",
            "",
            "=== AVAILABLE FLOWS ==="
        ]
        
        sorted_flows = sorted(
            self.routing_flows.items(), 
            key=lambda x: x[1].get('id', 99)
        )
        
        for i, (key, data) in enumerate(sorted_flows, 1):
            desc = data.get("description", "")
            keywords = data.get("strict_keywords", [])
            keyword_str = f" [Keywords: {', '.join(keywords[:3])}...]" if keywords else ""
            prompt_lines.append(f"{i}. {key}{keyword_str}")
            prompt_lines.append(f"   {desc}")
        
        prompt_lines.append(f"\n{len(sorted_flows)+1}. general (Greeting, chitchat, unclear intent)")
        
        prompt_lines.extend([
            "",
            "=== EXAMPLES ===",
            "User: 'I need to block my card' → card_atm_issues",
            "User: 'My card was stolen' → card_atm_issues",
            "User: 'What is my balance?' → account_servicing",
            "User: 'Show my transactions' → account_servicing",
            "User: 'I lost my card and want to check balance' → card_atm_issues (card safety priority)",
            "User: 'Hello' → general",
            "",
            "Output ONLY the flow name, nothing else."
        ])
        
        return "\n".join(prompt_lines)
    
    def get_flow_instructions(self, flow_name: str) -> Dict:
        """
        Get detailed flow instructions for a specific flow.
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            Dictionary with flow instructions (pre_verification, post_verification, edge_cases)
        """
        flow_data = self.routing_flows.get(flow_name, {})
        return flow_data.get("flow_instructions", {})
    
    def get_conversation_strategy(self, flow_name: str) -> Dict:
        """
        Get conversation strategy for a specific flow.
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            Dictionary with strategy info (approach, max_turns, escalation_triggers)
        """
        flow_data = self.routing_flows.get(flow_name, {})
        return flow_data.get("conversation_strategy", {})
    
    def is_deep_flow(self, flow_name: str) -> bool:
        """
        Automatically determine if a flow is deep/instructive based on its configuration.
        
        A flow is considered "deep" if:
        - It has multiple tools (beyond just verification)
        - AND/OR has detailed flow_instructions with pre/post verification steps
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            True if flow has tools and detailed instructions (deep/instructive)
            False if minimal tools/instructions (shallow/escalation)
        """
        flow_data = self.routing_flows.get(flow_name, {})
        
        # Check if flow has meaningful tools (beyond just t_verify_identity)
        tools = flow_data.get("tools", [])
        has_actionable_tools = len([t for t in tools if t != "t_verify_identity"]) > 0
        
        # Check if flow has detailed instructions
        flow_instructions = flow_data.get("flow_instructions", {})
        has_detailed_instructions = bool(
            flow_instructions.get("post_verification") or 
            flow_instructions.get("pre_verification")
        )
        
        # Flow is deep if it has tools to work with OR detailed instructions
        return has_actionable_tools or has_detailed_instructions
    
    def get_max_questions_before_escalation(self, flow_name: str) -> int | None:
        """
        Get maximum questions allowed before escalation for shallow flows.
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            Max questions count, or None for unlimited (deep flows)
        """
        flow_data = self.routing_flows.get(flow_name, {})
        return flow_data.get("max_questions_before_escalation")
    
    def get_escalation_message(self, flow_name: str) -> str:
        """
        Get the appropriate escalation message for a flow.
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            Escalation message string
        """
        # First check flow-specific instructions
        flow_data = self.routing_flows.get(flow_name, {})
        flow_instructions = flow_data.get("flow_instructions", {})
        if "escalation_message" in flow_instructions:
            return flow_instructions["escalation_message"]
        
        # Check escalation_message_templates for flow-specific messages
        templates = self.escalation_strategies.get("escalation_message_templates", {})
        if flow_name in templates:
            return templates[flow_name]
        
        # Default escalation message based on flow type
        if self.is_deep_flow(flow_name):
            return self.escalation_strategies.get(
                "deep_flows_default_message",
                "Let me connect you to one of our specialists who can assist you further."
            )
        else:
            return self.escalation_strategies.get(
                "shallow_flows_default_message", 
                "Let me connect you to a specialist who can help you with this."
            )
    
    def get_verification_prompt(self, prompt_type: str = "initial_request") -> str:
        """
        Get verification prompt message.
        
        Args:
            prompt_type: Type of verification prompt (initial_request, success_message, failure_message, alternative_method)
            
        Returns:
            Verification prompt string
        """
        default_prompts = {
            "initial_request": "For your security, I'll need to verify your identity. May I have your Account Number and PIN?",
            "success_message": "Thank you! Your identity has been verified successfully.",
            "failure_message": "I'm sorry, but I couldn't verify your identity. Please try again.",
            "alternative_method": "You can also provide your Phone Number for verification."
        }
        return self.verification_prompts.get(prompt_type, default_prompts.get(prompt_type, ""))
