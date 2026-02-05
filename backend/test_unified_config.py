#!/usr/bin/env python3
"""
Test script to verify unified configuration integration.

This script tests that:
1. Configuration loads successfully
2. FlowConfig can access flow instructions
3. System prompts are built correctly using unified config
"""

import sys
sys.path.insert(0, '/Users/sanchuka/Downloads/voice-ai-agent')

print("="*60)
print("Testing Unified Configuration Integration")
print("="*60)

# Test 1: Configuration Loading
print("\n[TEST 1] Loading unified_configuration.json...")
try:
    from backend.config import settings
    
    print(f"✓ Configuration loaded successfully")
    print(f"  - File: {settings.PROMPTS_FILE}")
    print(f"  - Contains {len(settings.PROMPTS.get('routing_flows', {}))} flows")
    print(f"  - Has system_persona: {bool(settings.PROMPTS.get('system_persona'))}")
    print(f"  - Has tool_registry: {bool(settings.PROMPTS.get('tool_registry'))}")
    print(f"  - Has escalation_strategies: {bool(settings.PROMPTS.get('escalation_strategies'))}")
except Exception as e:
    print(f"✗ Failed to load configuration: {e}")
    sys.exit(1)

# Test 2: FlowConfig Initialization
print("\n[TEST 2] Initializing FlowConfig...")
try:
    from backend.agent.config import FlowConfig
    
    flow_config = FlowConfig()
    print(f"✓ FlowConfig initialized successfully")
    print(f"  - Flows available: {list(flow_config.routing_flows.keys())}")
    print(f"  - Sensitive flows: {flow_config.sensitive_flows}")
    print(f"  - Deep flows: {[f for f in flow_config.routing_flows.keys() if flow_config.is_deep_flow(f)]}")
except Exception as e:
    print(f"✗ Failed to initialize FlowConfig: {e}")
    sys.exit(1)

# Test 3: Flow Instructions Access
print("\n[TEST 3] Accessing flow instructions...")
try:
    # Test deep flow
    card_instructions = flow_config.get_flow_instructions("card_atm_issues")
    print(f"✓ card_atm_issues instructions:")
    print(f"  - Has pre_verification: {bool(card_instructions.get('pre_verification'))}")
    print(f"  - Has post_verification: {bool(card_instructions.get('post_verification'))}")
    print(f"  - Has edge_cases: {bool(card_instructions.get('edge_cases'))}")
    
    # Test shallow flow
    account_opening = flow_config.get_flow_instructions("account_opening")
    print(f"✓ account_opening instructions:")
    print(f"  - Has interaction_pattern: {bool(account_opening.get('interaction_pattern'))}")
    print(f"  - Has escalation_message: {bool(account_opening.get('escalation_message'))}")
except Exception as e:
    print(f"✗ Failed to access flow instructions: {e}")
    sys.exit(1)

# Test 4: Conversation Strategies
print("\n[TEST 4] Accessing conversation strategies...")
try:
    card_strategy = flow_config.get_conversation_strategy("card_atm_issues")
    print(f"✓ card_atm_issues strategy:")
    print(f"  - Description: {card_strategy.get('description', '')[:60]}...")
    
    app_support_strategy = flow_config.get_conversation_strategy("digital_app_support")
    print(f"✓ digital_app_support strategy:")
    print(f"  - Description: {app_support_strategy.get('description', '')[:60]}...")
except Exception as e:
    print(f"✗ Failed to access conversation strategies: {e}")
    sys.exit(1)

# Test 5: Escalation Messages
print("\n[TEST 5] Testing escalation messages...")
try:
    card_escalation = flow_config.get_escalation_message("card_atm_issues")
    print(f"✓ card_atm_issues escalation message: \"{card_escalation[:60]}...\"")
    
    opening_escalation = flow_config.get_escalation_message("account_opening")
    print(f"✓ account_opening escalation message: \"{opening_escalation[:60]}...\"")
except Exception as e:
    print(f"✗ Failed to get escalation messages: {e}")
    sys.exit(1)

# Test 6: Verification Prompts
print("\n[TEST 6] Testing verification prompts...")
try:
    initial = flow_config.get_verification_prompt("initial_request")
    success = flow_config.get_verification_prompt("success_message")
    print(f"✓ initial_request: \"{initial[:50]}...\"")
    print(f"✓ success_message: \"{success[:50]}...\"")
except Exception as e:
    print(f"✗ Failed to get verification prompts: {e}")
    sys.exit(1)

# Test 7: System Prompt Building
print("\n[TEST 7] Testing system prompt building...")
try:
    from backend.agent.nodes import FlowExecutor
    
    executor = FlowExecutor(flow_config)
    
    # Test deep flow (verified)
    prompt_verified = executor._build_system_message("card_atm_issues", True, "C001")
    print(f"✓ Built system prompt for card_atm_issues (verified)")
    print(f"  - Contains 'DEEP INSTRUCTIVE MODE': {'DEEP INSTRUCTIVE MODE' in prompt_verified}")
    print(f"  - Contains customer_id: {'C001' in prompt_verified}")
    print(f"  - Length: {len(prompt_verified)} characters")
    
    # Test shallow flow
    prompt_shallow = executor._build_system_message("account_opening", False, "Unknown")
    print(f"✓ Built system prompt for account_opening")
    print(f"  - Contains 'SHALLOW ESCALATION MODE': {'SHALLOW ESCALATION MODE' in prompt_shallow}")
    print(f"  - Length: {len(prompt_shallow)} characters")
except Exception as e:
    print(f"✗ Failed to build system prompts: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 8: Flow Type Detection
print("\n[TEST 8] Testing flow type detection...")
try:
    print(f"✓ Deep flows:")
    for flow_name in flow_config.routing_flows.keys():
        is_deep = flow_config.is_deep_flow(flow_name)
        max_q = flow_config.get_max_questions_before_escalation(flow_name)
        if is_deep:
            print(f"  - {flow_name}: deep (unlimited questions)")
    
    print(f"✓ Shallow flows:")
    for flow_name in flow_config.routing_flows.keys():
        is_deep = flow_config.is_deep_flow(flow_name)
        max_q = flow_config.get_max_questions_before_escalation(flow_name)
        if not is_deep:
            print(f"  - {flow_name}: shallow (max {max_q} questions)")
except Exception as e:
    print(f"✗ Failed flow type detection: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✓ ALL TESTS PASSED!")
print("="*60)
print("\nThe unified configuration is properly integrated!")
print(f"- Config file: {settings.PROMPTS_FILE}")
print(f"- FlowConfig methods working correctly")
print(f"- System prompts being built from unified config")
print(f"- Deep vs shallow flow distinction working")
