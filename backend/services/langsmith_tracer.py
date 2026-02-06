"""
Centralized LangSmith Tracing Service

Provides consistent tracing configuration across all agent operations.
Each operation type has dedicated helpers for proper organization and labeling.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from backend.config import settings


class LangSmithTracer:
    """
    Centralized service for managing LangSmith tracing across the application.

    Features:
    - Consistent run naming conventions
    - Standardized metadata for all operations
    - Helper methods for different operation types
    - Proper parent-child trace relationships
    """

    def __init__(self):
        self.project_name = settings.LANGCHAIN_PROJECT
        self.is_enabled = settings.LANGCHAIN_TRACING_V2

    def initialize(self):
        """Initialize LangSmith tracing with environment variables."""
        if self.is_enabled:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = self.project_name
            print(f"LangSmith Tracing Enabled: {self.project_name}")
        else:
            print("LangSmith Tracing Disabled")

    # ========== Run Name Generators ==========

    def _generate_run_name(self, operation: str, context: Optional[str] = None) -> str:
        """
        Generate consistent run names for traces.

        Format: [Operation] Context
        Example: [Router] intent_classification

        Args:
            operation: The type of operation (e.g., "Router", "Executor")
            context: Optional context string (e.g., flow name, tool name)

        Returns:
            Formatted run name
        """
        if not context:
            context = "main"
        return f"[{operation}] {context}"

    # ========== Metadata Builders ==========

    def _build_base_metadata(
        self,
        call_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        is_verified: Optional[bool] = None,
        **extra
    ) -> Dict[str, Any]:
        """Build base metadata that should be present in all traces."""
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": self.project_name,
        }

        if call_id:
            metadata["call_id"] = call_id
        if customer_id:
            metadata["customer_id"] = customer_id
        if is_verified is not None:
            metadata["is_verified"] = is_verified

        # Add any extra metadata
        metadata.update(extra)

        return metadata

    # ========== Configuration Builders ==========

    def get_websocket_config(
        self,
        call_id: str,
        customer_id: Optional[str] = None,
        is_verified: bool = False,
        **extra
    ) -> Dict[str, Any]:
        """
        Get tracing config for WebSocket conversation invocations.

        This is the root-level trace that contains all sub-operations.

        Args:
            call_id: Unique identifier for this call session
            customer_id: Customer ID if known
            is_verified: Whether customer is verified
            **extra: Additional metadata to include

        Returns:
            Config dict for LangChain/LangGraph invoke
        """
        return {
            "run_name": self._generate_run_name("WebSocket", call_id[:8]),
            "tags": [
                "websocket",
                "conversation",
                "voice_agent",
                f"verified:{is_verified}",
            ],
            "metadata": self._build_base_metadata(
                call_id=call_id,
                customer_id=customer_id,
                is_verified=is_verified,
                operation="websocket_conversation",
                **extra
            ),
        }

    def get_router_config(
        self,
        call_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        current_flow: Optional[str] = None,
        **extra
    ) -> Dict[str, Any]:
        """
        Get tracing config for Router node operations.

        Args:
            call_id: Call session ID
            customer_id: Customer ID if known
            current_flow: Current active flow
            **extra: Additional metadata

        Returns:
            Config dict for LangChain invoke
        """
        return {
            "run_name": self._generate_run_name("Router", "intent_classification"),
            "tags": [
                "router",
                "classification",
                "intent_detection",
                f"current_flow:{current_flow}" if current_flow else "flow:unknown",
            ],
            "metadata": self._build_base_metadata(
                call_id=call_id,
                customer_id=customer_id,
                operation="router_classification",
                current_flow=current_flow,
                **extra
            ),
        }

    def get_executor_config(
        self,
        flow: str,
        call_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        is_verified: bool = False,
        tool_count: int = 0,
        **extra
    ) -> Dict[str, Any]:
        """
        Get tracing config for Flow Executor operations.

        Args:
            flow: Active flow name
            call_id: Call session ID
            customer_id: Customer ID if known
            is_verified: Whether customer is verified
            tool_count: Number of tools available
            **extra: Additional metadata

        Returns:
            Config dict for LangChain invoke
        """
        return {
            "run_name": self._generate_run_name("Executor", flow),
            "tags": [
                "executor",
                "conversation",
                f"flow:{flow}",
                f"verified:{is_verified}",
                f"tools:{tool_count}",
            ],
            "metadata": self._build_base_metadata(
                call_id=call_id,
                customer_id=customer_id,
                is_verified=is_verified,
                operation="flow_execution",
                active_flow=flow,
                tool_count=tool_count,
                **extra
            ),
        }

    def get_tool_config(
        self,
        tool_name: str,
        call_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        flow: Optional[str] = None,
        **extra
    ) -> Dict[str, Any]:
        """
        Get tracing config for Tool executions.

        Args:
            tool_name: Name of the tool being executed
            call_id: Call session ID
            customer_id: Customer ID
            flow: Active flow
            **extra: Additional metadata

        Returns:
            Config dict for tool tracing
        """
        return {
            "run_name": self._generate_run_name("Tool", tool_name),
            "tags": [
                "tool",
                "tool_execution",
                f"tool:{tool_name}",
                f"flow:{flow}" if flow else "flow:unknown",
            ],
            "metadata": self._build_base_metadata(
                call_id=call_id,
                customer_id=customer_id,
                operation="tool_execution",
                tool_name=tool_name,
                active_flow=flow,
                **extra
            ),
        }

    def get_verification_config(
        self,
        call_id: Optional[str] = None,
        flow: Optional[str] = None,
        **extra
    ) -> Dict[str, Any]:
        """
        Get tracing config for Verification Gate operations.

        Args:
            call_id: Call session ID
            flow: Flow requiring verification
            **extra: Additional metadata

        Returns:
            Config dict for verification tracing
        """
        return {
            "run_name": self._generate_run_name("Verification", "gate_check"),
            "tags": [
                "verification",
                "security",
                "gate",
                f"flow:{flow}" if flow else "flow:unknown",
            ],
            "metadata": self._build_base_metadata(
                call_id=call_id,
                operation="verification_gate",
                active_flow=flow,
                **extra
            ),
        }

    # ========== Utility Methods ==========

    def add_tags_to_config(self, config: Dict[str, Any], tags: List[str]) -> Dict[str, Any]:
        """Add additional tags to an existing config."""
        if "tags" not in config:
            config["tags"] = []
        config["tags"].extend(tags)
        return config

    def add_metadata_to_config(self, config: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Add additional metadata to an existing config."""
        if "metadata" not in config:
            config["metadata"] = {}
        config["metadata"].update(metadata)
        return config

    def enrich_config_with_context(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich a config with context from agent state.

        Automatically extracts common fields from state and adds them to metadata.
        """
        enriched_config = config.copy()

        # Extract common state fields
        if "customer_id" in state and state["customer_id"]:
            enriched_config.setdefault("metadata", {})["customer_id"] = state["customer_id"]

        if "is_verified" in state:
            enriched_config.setdefault("metadata", {})["is_verified"] = state["is_verified"]

        if "active_flow" in state:
            enriched_config.setdefault("metadata", {})["active_flow"] = state["active_flow"]

        return enriched_config


# Global singleton instance
tracer = LangSmithTracer()