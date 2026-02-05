"""
Agent Tools

Tool functions that interact with the database.
All tools now use SQLite instead of JSON files.
"""

from typing import Optional, Dict, List, Any

from backend.db import (
    verify_customer_credentials,
    get_customer_by_id,
    get_transactions_by_customer,
    update_customer_balance,
    block_customer_card
)


def verify_identity(
    customer_id: str | None = None, 
    account_number: str | None = None, 
    phone: str | None = None, 
    pin: str = ""
) -> str | bool:
    """
    Verifies customer identity via ID, Account Number, or Phone.
    
    Args:
        customer_id: Customer ID
        account_number: 4-digit account number
        phone: Phone number
        pin: 4-digit PIN
    
    Returns:
        Success message with customer ID if verified, False otherwise
    """
    customer = verify_customer_credentials(
        customer_id=customer_id,
        account_number=account_number,
        phone=phone,
        pin=pin
    )
    
    if customer:
        return f"Identity Verified successfully. Customer ID: {customer['id']}"
    return False


def get_recent_transactions(customer_id: str, count: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches recent transactions for a customer.
    
    Args:
        customer_id: Customer ID
        count: Number of transactions to fetch (default: 5)
    
    Returns:
        List of transaction dictionaries
    """
    return get_transactions_by_customer(customer_id, limit=count)


def block_card(card_id: str, reason: str = "User requested") -> bool:
    """
    Blocks a card (irreversible).
    
    Args:
        card_id: Card ID to block
        reason: Reason for blocking (logged but not stored currently)
    
    Returns:
        True if card was blocked, False otherwise
    """
    return block_customer_card(card_id)


def get_account_balance(customer_id: str) -> float:
    """
    Fetches current account balance.
    
    Args:
        customer_id: Customer ID
    
    Returns:
        Current balance as float
    """
    customer = get_customer_by_id(customer_id)
    return customer.get('balance', 0.0) if customer else 0.0


# Re-export for backward compatibility
__all__ = [
    'verify_identity',
    'get_recent_transactions',
    'block_card',
    'get_account_balance',
    'get_customer_by_id'
]
