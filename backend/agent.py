import json
from typing import Annotated, TypedDict, Literal, List
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from backend.config import settings
from backend.tools import verify_identity, get_recent_transactions, block_card, get_account_balance, get_customer_by_id

# --- TOOLS ---

@tool
def t_verify_identity(account_number: str = None, phone: str = None, customer_id: str = None, pin: str = None) -> str:
    """Verifies customer identity. Ask for Account Number (4 digits) and PIN usually. 
    Can also use Phone or Customer ID."""
    # Use whatever was provided
    result = verify_identity(customer_id=customer_id, account_number=account_number, phone=phone, pin=pin)
    if result:
         # Result is the success string containing ID
         return result
    return "Identity Verification Failed. Please check the details provided."

@tool
def t_get_balance(customer_id: str) -> str:
    """Gets account balance. Requires customer_id (context)."""
    bal = get_account_balance(customer_id)
    return f"Current balance is ${bal}"

@tool
def t_get_transactions(customer_id: str) -> str:
    """Gets recent transactions. Requires customer_id (context)."""
    txs = get_recent_transactions(customer_id)
    return json.dumps(txs)

@tool
def t_block_card(card_id: str) -> str:
    """Blocks a card. Requires card_id."""
    if block_card(card_id):
        return "Card blocked successfully."
    return "Failed to block card."

@tool
def t_end_call() -> str:
    """Terminates the current call."""
    return "Call terminated."

# -- New Placeholder Tools for other flows --
@tool
def t_check_eligibility(product_type: str) -> str:
    """Checks eligibility for new accounts/products."""
    return f"You are eligible for {product_type}. We can proceed with scheduling an appointment."

@tool
def t_support_ticket(issue_type: str, description: str) -> str:
    """Logs a support ticket for digital app issues."""
    return f"Ticket created for {issue_type}: {description}. IT will contact you shortly."

@tool
def t_transfer_funds(amount: float, beneficiary: str) -> str:
    """Transfers funds. (Mock)"""
    return f"Transfer of ${amount} to {beneficiary} initiated successfully."

@tool
def t_close_account_request(reason: str) -> str:
    """Logs an account closure request."""
    return f"Closure request logged. Reason: {reason}. A retention specialist will call you."

# --- CONFIG & SETUP ---

# 1. Tool Registry for Dynamic Loading
TOOL_REGISTRY = {
    "t_verify_identity": t_verify_identity,
    "t_get_balance": t_get_balance,
    "t_get_transactions": t_get_transactions,
    "t_block_card": t_block_card,
    "t_check_eligibility": t_check_eligibility,
    "t_support_ticket": t_support_ticket,
    "t_transfer_funds": t_transfer_funds,
    "t_close_account_request": t_close_account_request,
    "t_end_call": t_end_call
}

# 2. Load Flows from Prompts
routing_flows = settings.PROMPTS.get("routing_flows", {})

# 3. Dynamic FLOW_TOOLS Mapping
FLOW_TOOLS = {}
for flow_key, flow_data in routing_flows.items():
    tool_names = flow_data.get("tools", [])
    # Map string names to actual functions, filter invalid
    mapped_tools = [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]
    FLOW_TOOLS[flow_key] = mapped_tools

# Add 'general' flow fallback if not present
if "general" not in FLOW_TOOLS:
    FLOW_TOOLS["general"] = [t_verify_identity]

# 4. Dynamic Sensitive Flows List
SENSITIVE_FLOWS = [
    key for key, data in routing_flows.items() 
    if data.get("requires_verification", False)
]

# --- STATE ---

from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    customer_id: str | None
    account_number: str | None # For context
    is_verified: bool
    is_call_over: bool
    active_flow: str # One of the 6 flows or 'general'

# --- NODES ---

def router_node(state: AgentState):
    """Classifies the intent into one of the known flows."""
    messages = state['messages']
    
    # 5. Dynamic Router Prompt Construction
    prompt_lines = [
        "You are a banking router. Classify the user's latest intent into exactly one of these categories:"
    ]
    
    # helper for sorting consistently
    sorted_flows = sorted(routing_flows.items(), key=lambda x: x[1].get('id', 99))
    
    for i, (key, data) in enumerate(sorted_flows, 1):
        desc = data.get("description", "")
        prompt_lines.append(f"{i}. {key} ({desc})")
    
    prompt_lines.append(f"{len(sorted_flows)+1}. general (Greeting, other)") # Ensure general is always an option
    prompt_lines.append("\nOutput ONLY the category name. If uncertain or mixed, default to 'general'.")
    prompt_lines.append("If the user is continuing a previous conversation or answering a question, keep the context in mind.")
    
    system_prompt = "\n".join(prompt_lines)
    
    last_human = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if not last_human:
         return {"active_flow": "general"}

    # We can use a lightweight LLM call here
    llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0)
    classification = llm.invoke([SystemMessage(content=system_prompt), last_human]).content.strip().lower()
    
    # Sanitize
    valid_flows = FLOW_TOOLS.keys()
    if classification not in valid_flows:
        classification = "general"
        
    return {"active_flow": classification}

def verification_gate(state: AgentState):
    """
    Checks if the active flow requires verification.
    If so, and not verified, safeguards the next step.
    Updates state if verification just happened.
    """
    flow = state.get('active_flow', 'general')
    is_verified = state.get('is_verified', False)
    customer_id = state.get('customer_id', None)
    
    # Check if we successfully verified in the last turn (via tool output)
    messages = state['messages']
    if len(messages) > 0 and isinstance(messages[-1], ToolMessage):
        content = messages[-1].content
        if "Identity Verified successfully" in content:
            # Extract customer_id if present
            import re
            match = re.search(r"Customer ID: (\w+)", content)
            found_id = match.group(1) if match else None
            return {"is_verified": True, "customer_id": found_id}
            
    if flow in SENSITIVE_FLOWS and not is_verified:
        return {"messages": [SystemMessage(content="Current Flow requires VERIFICATION. You MUST ask for Account Number and PIN if not provided. Do not perform the action until verified.")]}
    
    return {}

def flow_executor(state: AgentState):
    """Executes the logic for the active flow."""
    flow = state.get('active_flow', 'general')
    messages = state['messages']
    is_verified = state.get('is_verified', False)
    customer_id = state.get('customer_id', "Unknown")
    
    flow_tools = FLOW_TOOLS.get(flow, FLOW_TOOLS['general'])
    if t_end_call not in flow_tools:
        flow_tools.append(t_end_call)
        
    llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=settings.LLM_TEMPERATURE).bind_tools(flow_tools)
    
    base_persona = settings.PROMPTS.get("system_persona", "You are a banking assistant.")
    
    workaround_instruction = (
        "\n\nIMPORTANT VERIFICATION NOTE: "
        "Can't hear 'Customer ID' well? Ask for 'Account Number' (4 digits) or 'Phone Number' instead. "
        "Prefer asking for Account Number and PIN for verification."
    )
    
    permission_note = ""
    if is_verified:
        permission_note = (
            f"\n\n[SYSTEM UPDATE]: User is VERIFIED (Customer ID: {customer_id}). "
            "You have permission to disclose account details, balances, and perform actions. "
            "Proceed with the user's request immediately."
        )

    sys_msg = f"{base_persona}\n\nCurrent Flow: {flow}\n{workaround_instruction}{permission_note}"
    
    # Safe invoke
    response = llm.invoke([SystemMessage(content=sys_msg)] + messages)
    
    is_call_over = False
    if response.tool_calls:
         for tc in response.tool_calls:
            if tc['name'] == 't_end_call':
                is_call_over = True
    
    return {"messages": [response], "is_call_over": is_call_over}

# --- GRAPH ---

workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("gate", verification_gate)
workflow.add_node("agent", flow_executor)

# Deduplicate tools
all_flow_tools = [t for tools in FLOW_TOOLS.values() for t in tools] + [t_end_call]
unique_tools = {}
for t in all_flow_tools:
    if t.name not in unique_tools:
        unique_tools[t.name] = t
all_tools = list(unique_tools.values())
workflow.add_node("tools", ToolNode(all_tools))

workflow.add_edge(START, "router")
workflow.add_edge("router", "gate")
workflow.add_edge("gate", "agent")

def should_continue(state: AgentState) -> Literal["tools", "__end__", "router"]:
    if state.get("is_call_over"):
        return "__end__"
        
    messages = state['messages']
    last_message = messages[-1]
    
    if last_message.tool_calls:
        return "tools"
    
    return "__end__"

workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "gate") 

app_graph = workflow.compile()
