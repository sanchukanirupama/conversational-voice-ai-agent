"""
Migration Script: JSON to SQLite

Migrates customer data from customers.json to SQLite database.
"""

import json
import os
from backend.db.database import init_db, create_customer, create_transaction
from backend.db.models import Customer, Transaction


def migrate_json_to_sqlite():
    """
    Migrate data from customers.json to SQLite database.
    """
    # Initialize database
    init_db()
    
    # Load JSON data
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'customers.json')
    
    if not os.path.exists(json_path):
        print(f"❌ customers.json not found at {json_path}")
        return
    
    with open(json_path, 'r') as f:
        customers_data = json.load(f)
    
    print(f"📦 Migrating {len(customers_data)} customers...")
    
    for customer_data in customers_data:
        try:
            # Map JSON fields to database fields
            db_customer = {
                'id': customer_data['customer_id'],
                'name': customer_data['name'],
                'account_number': customer_data['account_number'],
                'phone': customer_data['profile']['phone'],
                'pin': customer_data['pin'],
                'balance': customer_data.get('account_balance', 0.0),
                'card_id': customer_data.get('card_id'),
                'card_status': customer_data.get('card_status', 'active')
            }
            
            # Extract transactions
            transactions = customer_data.get('recent_transactions', [])
            
            # Create customer
            create_customer(db_customer)
            print(f"  ✓ Created customer: {db_customer['id']} ({db_customer['name']})")
            
            # Create transactions
            for txn in transactions:
                txn_data = {
                    'date': txn.get('date', ''),
                    'description': txn.get('description', ''),
                    'amount': abs(txn.get('amount', 0.0)),
                    'type': 'debit' if txn.get('amount', 0) < 0 else 'credit'
                }
                create_transaction(db_customer['id'], txn_data)
            
            if transactions:
                print(f"    ✓ Added {len(transactions)} transactions")
        
        except Exception as e:
            print(f"  ❌ Error migrating {customer_data.get('customer_id', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    migrate_json_to_sqlite()
