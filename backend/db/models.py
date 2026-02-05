"""
Database Models

SQLAlchemy models for the voice AI agent database.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Customer(Base):
    """Customer account information."""
    
    __tablename__ = 'customers'
    
    id = Column(String, primary_key=True)  # e.g., 'cust_001'
    name = Column(String, nullable=False)
    account_number = Column(String(4), unique=True, nullable=False)
    phone = Column(String, nullable=False)
    pin = Column(String(4), nullable=False)
    balance = Column(Float, default=0.0)
    card_id = Column(String)
    card_status = Column(String, default='active')  # 'active', 'blocked'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'name': self.name,
            'account_number': self.account_number,
            'phone': self.phone,
            'pin': self.pin,
            'balance': self.balance,
            'card_id': self.card_id,
            'card_status': self.card_status
        }


class Transaction(Base):
    """Transaction history for customers."""
    
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=False)
    date = Column(String, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # 'debit', 'credit'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'date': self.date,
            'description': self.description,
            'amount': self.amount,
            'type': self.type
        }
