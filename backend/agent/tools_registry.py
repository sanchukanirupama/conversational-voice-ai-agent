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
def t_block_card(customer_id: str) -> str:
    """Blocks the customer's active card immediately for security. 
    Use this when customer reports lost/stolen card or requests card blocking.
    Requires customer_id (you will have this after verification).
    The system will automatically find and block the customer's card."""
    from backend.tools import get_customer_by_id
    
    customer = get_customer_by_id(customer_id)
    if not customer:
        return "Failed to block card: Customer not found."
    
    card_id = customer.get('card_id')
    if not card_id:
        return "Failed to block card: No card found for this customer."
    
    if block_card(card_id):
        return f"Card ending in {card_id[-4:]} has been blocked successfully for security. A replacement card will be mailed within 5-7 business days."
    return "Failed to block card. Please try again or contact support."


@tool
def t_update_address(customer_id: str, new_address: str) -> str:
    """Updates the customer's address in their profile. 
    Use this when customer wants to change their mailing address.
    Requires customer_id (you will have this after verification) and the new address."""
    from backend.tools import update_address
    return update_address(customer_id, new_address)


@tool
def t_end_call() -> str:
    """Terminates the call. Use this when:
    1. User says goodbye, asks to hang up, or indicates they're done
    2. User says they don't need help or have no banking needs
    3. You've completed helping the user and they have no more questions
    4. Conversation has reached a natural conclusion

    IMPORTANT: ALWAYS call this tool immediately after saying your goodbye message."""
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
