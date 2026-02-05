"""
Flow Configuration

Manages flow definitions, tool mappings, and sensitive flow detection.
"""

from typing import Dict, List
from backend.config import settings
from backend.agent.tools_registry import TOOL_REGISTRY, t_verify_identity, t_end_call


class FlowConfig:
    """
    Manages flow configurations loaded from prompts.json.
    
    Responsibilities:
    - Load and parse flow definitions
    - Map tool names to tool objects
    - Identify flows requiring verification
    """
    
    def __init__(self):
        self.routing_flows = settings.PROMPTS.get("routing_flows", {})
        self.flow_tools = self._build_flow_tools()
        self.sensitive_flows = self._build_sensitive_flows()
    
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
