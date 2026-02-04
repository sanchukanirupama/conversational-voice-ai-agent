import json
from typing import Optional, Dict, List, Any

from backend.config import settings

def _load_customers() -> List[Dict[str, Any]]:
    with open(settings.CUSTOMERS_FILE, 'r') as f:
        return json.load(f)

def _save_customers(customers: List[Dict[str, Any]]):
    with open(settings.CUSTOMERS_FILE, 'w') as f:
        json.dump(customers, f, indent=2)

def verify_identity(customer_id: str, pin: str) -> bool:
    """Verifies customer identity check."""
    customers = _load_customers()
    for cust in customers:
        if cust['customer_id'] == customer_id and cust['pin'] == pin:
            return True
    return False

def get_recent_transactions(customer_id: str, count: int | None = None) -> List[Dict[str, Any]]:
    """Fetches recent transactions for a customer."""
    if count is None:
        count = settings.DEFAULT_TRANSACTION_COUNT
    customers = _load_customers()
    for cust in customers:
        if cust['customer_id'] == customer_id:
            return cust.get('recent_transactions', [])[:count]
    return []

def block_card(card_id: str, reason: str = "User requested") -> bool:
    """Blocks a card. Irreversible."""
    customers = _load_customers()
    updated = False
    for cust in customers:
        if cust.get('card_id') == card_id:
            cust['card_status'] = 'blocked'
            updated = True
            break
    if updated:
        _save_customers(customers)
        return True
    return False

def get_account_balance(customer_id: str) -> float:
    """Fetches current account balance."""
    customers = _load_customers()
    for cust in customers:
        if cust['customer_id'] == customer_id:
            return cust.get('account_balance', 0.0)
    return 0.0

def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    customers = _load_customers()
    for cust in customers:
        if cust['customer_id'] == customer_id:
            return cust
    return None
