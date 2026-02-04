"""
Graph Builder

Constructs and compiles the LangGraph workflow.
"""

from typing import Literal
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from backend.agent.state import AgentState
from backend.agent.config import FlowConfig
from backend.agent.nodes import RouterNode, VerificationGate, FlowExecutor
from backend.agent.tools_registry import get_all_tools


class AgentGraphBuilder:
    """
    Builds the complete LangGraph workflow.

    """
    
    def __init__(self):
        self.flow_config = FlowConfig()
        self.router = RouterNode(self.flow_config)
        self.gate = VerificationGate(self.flow_config)
        self.executor = FlowExecutor(self.flow_config)
    
    def build(self):
        """
        Constructs and compiles the graph.
        
        Returns:
            Compiled LangGraph application
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", self.router)
        workflow.add_node("gate", self.gate)
        workflow.add_node("agent", self.executor)
        workflow.add_node("tools", ToolNode(get_all_tools()))
        
        # Add edges
        workflow.add_edge(START, "router")
        workflow.add_edge("router", "gate")
        workflow.add_edge("gate", "agent")
        workflow.add_conditional_edges("agent", self._should_continue)
        workflow.add_edge("tools", "gate")  # Loop back after tool execution
        
        return workflow.compile()
    
    def _should_continue(self, state: AgentState) -> Literal["tools", "__end__"]:
        """
        Decision function: Determines next step after agent response.
        
        Logic:
        - If is_call_over=True → END
        - If agent called tools → TOOLS node
        - Otherwise → END (pure text response)
        """
        if state.get("is_call_over"):
            return "__end__"
            
        messages = state['messages']
        last_message = messages[-1]
        
        if last_message.tool_calls:
            return "tools"
        
        return "__end__"
