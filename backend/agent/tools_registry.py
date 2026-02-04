"""
Tool Registry

Defines all available tools for the agent and manages tool-to-flow mappings.
"""

import json
from langchain_core.tools import tool
from backend.tools import verify_identity, get_recent_transactions, block_card, get_account_balance


@tool
def t_verify_identity(account_number: str = None, phone: str = None, customer_id: str = None, pin: str = None) -> str:
    """Verifies customer identity. Ask for Account Number (4 digits) and PIN usually. 
    Can also use Phone or Customer ID."""
    result = verify_identity(customer_id=customer_id, account_number=account_number, phone=phone, pin=pin)
    if result:
        return result
    return "Identity Verification Failed. Please check the details provided."


@tool
def t_get_balance(customer_id: str) -> str:
    """Gets the REAL account balance. You MUST use this tool to answer balance questions. 
    Do NOT guess. Requires customer_id."""
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
    """Terminates the call. ONLY use this if the user explicitly says goodbye or asks to hang up."""
    return "Call terminated."


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


# ============================================================================
# TOOL REGISTRY
# ============================================================================

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


def get_all_tools():
    """Returns a deduplicated list of all tools."""
    return list(TOOL_REGISTRY.values())
