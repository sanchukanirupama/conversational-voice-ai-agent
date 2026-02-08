"""
Startup Script

Initializes database and loads customer data on server startup.
"""

import json
import os
from backend.db.database import init_db, get_db
from backend.db.models import Customer, Transaction


def load_customers_from_json():
    """
    Load customers from customers.json and upsert into database.
    Creates database if it doesn't exist.
    """
    # Initialize database (creates tables if they don't exist)
    init_db()
    
    # Path to customers.json
    customers_file = os.path.join(
        os.path.dirname(__file__), 
        'data', 
        'customers.json'
    )
    
    if not os.path.exists(customers_file):
        print(f"customers.json not found at {customers_file}")
        return
    
    # Load customer data from JSON
    with open(customers_file, 'r') as f:
        customers_data = json.load(f)
    
    print(f"\n Upserting {len(customers_data)} customers into database...")
    
    with get_db() as db:
        upserted_count = 0
        updated_count = 0
        
        for customer_json in customers_data:
            # Map JSON fields to database fields
            customer_id = customer_json['customer_id']
            
            # Check if customer already exists
            existing_customer = db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if existing_customer:
                # Update existing customer
                existing_customer.name = customer_json['name']
                existing_customer.account_number = customer_json['account_number']
                existing_customer.phone = customer_json['profile']['phone']
                existing_customer.pin = customer_json['pin']
                existing_customer.balance = customer_json['account_balance']
                existing_customer.card_id = customer_json['card_id']
                existing_customer.card_status = customer_json['card_status']
                updated_count += 1
            else:
                # Create new customer
                new_customer = Customer(
                    id=customer_id,
                    name=customer_json['name'],
                    account_number=customer_json['account_number'],
                    phone=customer_json['profile']['phone'],
                    pin=customer_json['pin'],
                    balance=customer_json['account_balance'],
                    card_id=customer_json['card_id'],
                    card_status=customer_json['card_status']
                )
                db.add(new_customer)
                upserted_count += 1
            
            # Upsert transactions
            if 'recent_transactions' in customer_json:
                # Clear existing transactions for this customer
                db.query(Transaction).filter(
                    Transaction.customer_id == customer_id
                ).delete()
                
                # Add new transactions
                for txn_json in customer_json['recent_transactions']:
                    transaction = Transaction(
                        customer_id=customer_id,
                        date=txn_json['date'],
                        description=txn_json['description'],
                        amount=abs(txn_json['amount']),
                        type='debit' if txn_json['amount'] < 0 else 'credit'
                    )
                    db.add(transaction)
        
        db.commit()
    
    print(f"Database ready:")
    print(f"   - {upserted_count} new customers added")
    print(f"   - {updated_count} existing customers updated")
    print(f"   - Total customers: {upserted_count + updated_count}")


def startup():
    """
    Run all startup tasks.
    """
    print("\n" + "="*60)
    print("Starting Voice AI Backend...")
    print("="*60)
    
    load_customers_from_json()
    
    print("="*60)
    print("Backend startup complete!\n")
