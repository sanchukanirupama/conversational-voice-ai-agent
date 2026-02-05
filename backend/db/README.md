# SQLite Database Migration

This document explains the migration from JSON file storage to SQLite database.

## New Database Structure

```
backend/db/
├── __init__.py       # Module exports
├── models.py         # SQLAlchemy models (Customer, Transaction)
├── database.py       # Database operations (CRUD)
└── migrate.py        # Migration script (JSON → SQLite)
```

## Database Schema

### Customer Table
```sql
CREATE TABLE customers (
    id VARCHAR PRIMARY KEY,           -- e.g., 'cust_001'
    name VARCHAR NOT NULL,
    account_number VARCHAR(4) UNIQUE NOT NULL,
    phone VARCHAR NOT NULL,
    pin VARCHAR(4) NOT NULL,
    balance FLOAT DEFAULT 0.0,
    card_id VARCHAR,
    card_status VARCHAR DEFAULT 'active',
    created_at DATETIME,
    updated_at DATETIME
);
```

### Transaction Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id VARCHAR FOREIGN KEY,
    date VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    amount FLOAT NOT NULL,
    type VARCHAR NOT NULL,           -- 'debit' or 'credit'
    created_at DATETIME
);
```

## Migration Steps

1. **Run Migration Script:**
   ```bash
   python -m backend.db.migrate
   ```

2. **Verify Database:**
   ```bash
   sqlite3 backend/data/voice_agent.db "SELECT * FROM customers;"
   ```

## Updated Tools

All tools in `backend/tools.py` now use the database:

- ✅ `verify_identity()` - Queries customer table with PIN validation
- ✅ `get_account_balance()` - Fetches live balance from DB
- ✅ `get_recent_transactions()` - Queries transaction table
- ✅ `block_card()` - Updates card_status in database
- ✅ `get_customer_by_id()` - Database lookup

## Database Operations API

```python
from backend.db import (
    get_customer_by_id,
    verify_customer_credentials,
    update_customer_balance,
    block_customer_card,
    create_customer,
    get_transactions_by_customer,
    create_transaction
)

# Example: Verify customer
customer = verify_customer_credentials(
    account_number="1001",
    pin="1234"
)

# Example: Update balance
update_customer_balance("cust_001", 5000.00)

# Example: Block card
block_customer_card("card_9876")
```

## Agent Tool Updates

The agent can now:
- **Fetch** customer data (balance, transactions)
- **Update** data (block cards, modify balances)

All operations are atomic and use database transactions for consistency.

## Benefits

1. **Data Integrity**: ACID compliance, foreign keys, constraints
2. **Concurrency**: Multiple agents can safely access data
3. **Scalability**: Better performance for large datasets
4. **Query Power**: SQL queries for complex operations
5. **Audit Trail**: Automatic timestamps on all records

## Future Enhancements

Possible next steps:
- Add audit log table for all agent actions
- Implement customer history tracking
- Add indexes for performance
- Create admin dashboard queries
- Add data export/backup tools
