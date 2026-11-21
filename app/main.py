
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import Base, engine, get_db
from app.models import Customer, Transaction

# Database tables তৈরি
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Jahid Due Manager")

# Static files
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


# Customer-এর বর্তমান বাকি হিসাব
def get_balance(db: Session, customer_id: int):

    due = db.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.customer_id == customer_id,
        Transaction.transaction_type == "due"
    ).scalar()

    payment = db.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.customer_id == customer_id,
        Transaction.transaction_type == "payment"
    ).scalar()

    return float(due - payment)


# Homepage
@app.get("/")
def home():
    return FileResponse("app/static/index.html")


# Dashboard
@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):

    customers = db.query(Customer).all()

    total_due = sum(
        max(get_balance(db, c.id), 0)
        for c in customers
    )

    total_customers = len(customers)

    total_received = db.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.transaction_type == "payment"
    ).scalar()

    return {
        "total_due": round(total_due, 2),
        "total_customers": total_customers,
        "total_received": round(float(total_received), 2)
    }


# Customer list and search
@app.get("/api/customers")
def list_customers(
    search: str = "",
    db: Session = Depends(get_db)
):

    query = db.query(Customer)

    if search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (Customer.name.ilike(term)) |
            (Customer.phone.ilike(term))
        )

    customers = query.order_by(Customer.id.desc()).all()

    result = []

    for customer in customers:
        result.append({
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone or "",
            "address": customer.address or "",
            "balance": round(get_balance(db, customer.id), 2)
        })

    return result


# Add customer
@app.post("/api/customers")
def add_customer(
    data: dict,
    db: Session = Depends(get_db)
):

    name = str(data.get("name", "")).strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Customer name is required"
        )

    customer = Customer(
        name=name,
        phone=str(data.get("phone", "")).strip(),
        address=str(data.get("address", "")).strip()
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return {
        "message": "Customer added",
        "id": customer.id
    }


# Add due or payment
@app.post("/api/transactions")
def add_transaction(
    data: dict,
    db: Session = Depends(get_db)
):

    try:
        customer_id = int(data.get("customer_id"))
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid customer or amount"
        )

    transaction_type = str(data.get("type", "")).lower()

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be positive"
        )

    if transaction_type not in ["due", "payment"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid transaction type"
        )

    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    if transaction_type == "payment":
        balance = get_balance(db, customer_id)

        if amount > balance:
            raise HTTPException(
                status_code=400,
                detail=f"Payment exceeds outstanding balance: {balance} Tk"
            )

    transaction = Transaction(
        customer_id=customer_id,
        transaction_type=transaction_type,
        amount=amount,
        note=str(data.get("note", "")).strip()
    )

    db.add(transaction)
    db.commit()

    return {
        "message": "Transaction saved",
        "balance": round(get_balance(db, customer_id), 2)
    }


# Transaction history
@app.get("/api/transactions")
def transaction_history(
    customer_id: int = 0,
    transaction_type: str = "",
    db: Session = Depends(get_db)
):

    query = db.query(Transaction, Customer).join(
        Customer,
        Transaction.customer_id == Customer.id
    )

    if customer_id:
        query = query.filter(
            Transaction.customer_id == customer_id
        )

    if transaction_type in ["due", "payment"]:
        query = query.filter(
            Transaction.transaction_type == transaction_type
        )

    rows = query.order_by(
        Transaction.id.desc()
    ).limit(500).all()

    result = []

    for transaction, customer in rows:
        result.append({
            "id": transaction.id,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "type": transaction.transaction_type,
            "amount": transaction.amount,
            "note": transaction.note or "",
            "created_at": (
                transaction.created_at.isoformat()
                if transaction.created_at else ""
            )
        })

    return result
