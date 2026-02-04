"""
Voice AI Agent Module

A modular, class-based implementation of the LangGraph voice agent.

Architecture:
- state.py: State schema definition
- tools_registry.py: Tool definitions and registry
- config.py: Flow configuration management
- nodes.py: Router, Gate, and Executor node classes
- graph.py: Graph builder and compiler
- utils.py: Helper functions
"""

from backend.agent.graph import AgentGraphBuilder
from backend.agent.utils import generate_contextual_response

# Build and export the graph
_builder = AgentGraphBuilder()
app_graph = _builder.build()

__all__ = ['app_graph', 'generate_contextual_response']
