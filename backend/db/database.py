"""
Database Connection and Operations

Handles SQLite database connection and CRUD operations.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Optional, List, Dict
import os

from backend.db.models import Base, Customer, Transaction


# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'voice_agent.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with SQLite-specific settings for concurrent access
# - check_same_thread=False: Allows connections to be used across threads (needed for async/FastAPI)
# - timeout: Increases lock timeout to handle concurrent writes
# - poolclass: Use StaticPool to maintain a single connection and prevent I/O errors
# - connect_args: Enable WAL mode for better concurrency
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    connect_args={
        'check_same_thread': False,  # Allow cross-thread usage
        'timeout': 30.0,  # 30 second timeout for locks
    },
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Enable WAL mode for better concurrent access
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database initialized at {DB_PATH}")


@contextmanager
def get_db() -> Session:
    """
    Get database session with automatic cleanup.
    
    Usage:
        with get_db() as db:
            customer = db.query(Customer).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# ============================================================================
# CUSTOMER OPERATIONS
# ============================================================================

def get_customer_by_id(customer_id: str) -> Optional[Dict]:
    """Get customer by ID."""
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        return customer.to_dict() if customer else None


def get_customer_by_account_number(account_number: str) -> Optional[Dict]:
    """Get customer by account number."""
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.account_number == account_number).first()
        return customer.to_dict() if customer else None


def get_customer_by_phone(phone: str) -> Optional[Dict]:
    """Get customer by phone number."""
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        return customer.to_dict() if customer else None


def verify_customer_credentials(account_number: str = None, phone: str = None, 
                                customer_id: str = None, pin: str = None) -> Optional[Dict]:
    """
    Verify customer credentials and return customer data if valid.
    
    Args:
        account_number: 4-digit account number
        phone: Phone number
        customer_id: Customer ID
        pin: 4-digit PIN
    
    Returns:
        Customer dict if credentials valid, None otherwise
    """
    with get_db() as db:
        query = db.query(Customer)
        
        # Build query based on provided identifiers
        if customer_id:
            query = query.filter(Customer.id == customer_id)
        elif account_number:
            query = query.filter(Customer.account_number == account_number)
        elif phone:
            query = query.filter(Customer.phone == phone)
        else:
            return None
        
        customer = query.first()
        
        # Verify PIN if customer found
        if customer and pin and customer.pin == pin:
            return customer.to_dict()
        
        return None


def update_customer_balance(customer_id: str, new_balance: float) -> bool:
    """Update customer balance."""
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.balance = new_balance
            return True
        return False


def block_customer_card(card_id: str) -> bool:
    """Block a customer's card."""
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.card_id == card_id).first()
        if customer:
            customer.card_status = 'blocked'
            return True
        return False


def create_customer(customer_data: Dict) -> Customer:
    """Create a new customer."""
    with get_db() as db:
        customer = Customer(**customer_data)
        db.add(customer)
        db.flush()
        return customer.to_dict()


# ============================================================================
# TRANSACTION OPERATIONS
# ============================================================================

def get_transactions_by_customer(customer_id: str, limit: int = 10) -> List[Dict]:
    """Get recent transactions for a customer."""
    with get_db() as db:
        transactions = (
            db.query(Transaction)
            .filter(Transaction.customer_id == customer_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .all()
        )
        return [t.to_dict() for t in transactions]


def create_transaction(customer_id: str, transaction_data: Dict) -> Transaction:
    """Create a new transaction."""
    with get_db() as db:
        transaction = Transaction(customer_id=customer_id, **transaction_data)
        db.add(transaction)
        db.flush()
        return transaction.to_dict()


def get_all_customers() -> List[Dict]:
    """Get all customers (for admin/migration purposes)."""
    with get_db() as db:
        customers = db.query(Customer).all()
        return [c.to_dict() for c in customers]
