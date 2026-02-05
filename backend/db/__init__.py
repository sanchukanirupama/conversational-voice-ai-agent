"""
Database module initialization.
"""

from backend.db.database import (
    init_db,
    get_db,
    get_customer_by_id,
    get_customer_by_account_number,
    get_customer_by_phone,
    verify_customer_credentials,
    update_customer_balance,
    block_customer_card,
    create_customer,
    get_transactions_by_customer,
    create_transaction,
    get_all_customers
)

__all__ = [
    'init_db',
    'get_db',
    'get_customer_by_id',
    'get_customer_by_account_number',
    'get_customer_by_phone',
    'verify_customer_credentials',
    'update_customer_balance',
    'block_customer_card',
    'create_customer',
    'get_transactions_by_customer',
    'create_transaction',
    'get_all_customers'
]
