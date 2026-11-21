

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(120), nullable=False)

    phone = Column(String(30), nullable=True)

    address = Column(String(250), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    transactions = relationship(
        "Transaction",
        back_populates="customer",
        cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    transaction_type = Column(String(20), nullable=False)

    amount = Column(Float, nullable=False)

    note = Column(String(250), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    customer = relationship(
        "Customer",
        back_populates="transactions"
    )
