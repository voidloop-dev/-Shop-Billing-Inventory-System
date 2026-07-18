"""
Business logic for the Shop Billing & Inventory System.
All money/stock math lives here — completely separate from the GUI.
"""

import hashlib
import shutil
import os
from datetime import datetime, date
from models import (
    Product, StockMovement, Customer, Sale, SaleItem,
    Payment, Setting, next_invoice_number
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


def get_setting(session, key: str, default="") -> str:
    s = session.query(Setting).filter_by(key=key).first()
    return s.value if s else default


def set_setting(session, key: str, value: str):
    s = session.query(Setting).filter_by(key=key).first()
    if s:
        s.value = value
    else:
        session.add(Setting(key=key, value=value))
    session.commit()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def is_password_set(session) -> bool:
    return bool(get_setting(session, "password_hash"))


def set_password(session, new_password: str):
    set_setting(session, "password_hash", hash_password(new_password))


def verify_login(session, password: str) -> bool:
    stored = get_setting(session, "password_hash")
    if not stored:
        return True   # first run — no password set yet
    return check_password(password, stored)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def _get_product(session, product_id):
    """SQLAlchemy-2-safe primary key lookup."""
    return session.query(Product).filter_by(id=product_id).first()


def _get_customer(session, customer_id):
    return session.query(Customer).filter_by(id=customer_id).first()


def get_all_products(session, include_inactive=False):
    q = session.query(Product)
    if not include_inactive:
        q = q.filter(Product.is_active == True)
    return q.order_by(Product.name).all()


def search_products(session, query: str):
    q = session.query(Product).filter(Product.is_active == True)
    if query:
        like = f"%{query}%"
        q = q.filter(
            Product.name.ilike(like) |
            Product.category.ilike(like) |
            Product.size_value.ilike(like)
        )
    return q.order_by(Product.name).all()


def add_product(session, name, category, unit, size_value, size_unit,
                cost_price, selling_price, initial_stock, low_stock_threshold) -> Product:
    p = Product(
        name=name, category=category, unit=unit,
        size_value=size_value, size_unit=size_unit,
        cost_price=float(cost_price),
        selling_price=float(selling_price),
        current_stock=float(initial_stock),
        low_stock_threshold=float(low_stock_threshold),
    )
    session.add(p)
    session.flush()
    if float(initial_stock) > 0:
        session.add(StockMovement(
            product_id=p.id, movement_type="IN",
            quantity=float(initial_stock), note="Initial stock"
        ))
    session.commit()
    return p


def update_product(session, product_id, **kwargs) -> Product:
    p = _get_product(session, product_id)
    for k, v in kwargs.items():
        setattr(p, k, v)
    p.updated_at = datetime.now()
    session.commit()
    return p


def deactivate_product(session, product_id):
    p = _get_product(session, product_id)
    p.is_active = False
    session.commit()


def get_low_stock_products(session):
    """Products where stock is BELOW (not equal to) threshold — avoids showing
    items at exactly the threshold as 'low' when threshold is 0."""
    products = get_all_products(session)
    return [p for p in products if p.current_stock < p.low_stock_threshold]


# ---------------------------------------------------------------------------
# Stock In
# ---------------------------------------------------------------------------

def stock_in(session, product_id, quantity, note="") -> StockMovement:
    qty = float(quantity)
    if qty <= 0:
        raise ValueError("Quantity must be greater than zero.")
    p = _get_product(session, product_id)
    p.current_stock = round(p.current_stock + qty, 4)
    p.updated_at = datetime.now()
    mv = StockMovement(product_id=product_id, movement_type="IN",
                       quantity=qty, note=note)
    session.add(mv)
    session.commit()
    return mv


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

def get_all_customers(session):
    return session.query(Customer).order_by(Customer.name).all()


def search_customers(session, query: str):
    q = session.query(Customer)
    if query:
        like = f"%{query}%"
        q = q.filter(
            Customer.name.ilike(like) | Customer.phone.ilike(like)
        )
    return q.order_by(Customer.name).all()


def add_customer(session, name, phone="", address="",
                 default_discount=0.0) -> Customer:
    c = Customer(name=name, phone=phone, address=address,
                 default_discount=float(default_discount))
    session.add(c)
    session.commit()
    return c


def update_customer(session, customer_id, **kwargs) -> Customer:
    c = _get_customer(session, customer_id)
    for k, v in kwargs.items():
        setattr(c, k, v)
    session.commit()
    return c


def record_payment(session, customer_id, amount,
                   note="", sale_id=None) -> Payment:
    amt = float(amount)
    if amt <= 0:
        raise ValueError("Payment amount must be greater than zero.")
    c = _get_customer(session, customer_id)
    if c.due_balance <= 0:
        raise ValueError("This customer has no outstanding balance.")
    # Cap at actual balance — never go negative
    amt = min(amt, c.due_balance)
    c.due_balance = round(c.due_balance - amt, 2)
    pmt = Payment(customer_id=customer_id, amount=amt,
                  note=note, sale_id=sale_id)
    session.add(pmt)
    session.commit()
    return pmt


# ---------------------------------------------------------------------------
# Billing / Sales
# ---------------------------------------------------------------------------

def compute_discount(subtotal: float, discount_type: str,
                     discount_value: float) -> float:
    """Return the discount AMOUNT to subtract from subtotal."""
    if discount_type == "percent":
        # Clamp percentage to 0–100
        pct = max(0.0, min(float(discount_value), 100.0))
        return round(subtotal * (pct / 100), 2)
    else:
        # Flat — cannot exceed subtotal, cannot be negative
        return round(min(max(float(discount_value), 0.0), subtotal), 2)


def create_sale(session, customer_id, items, discount_type,
                discount_value, amount_paid, notes="") -> Sale:
    if not items:
        raise ValueError("A sale must have at least one item.")

    amount_paid = max(float(amount_paid), 0.0)

    subtotal = round(sum(float(i["quantity"]) * float(i["unit_price"])
                         for i in items), 2)
    discount_amount = compute_discount(subtotal, discount_type,
                                       float(discount_value))
    total = round(subtotal - discount_amount, 2)
    # Amount paid cannot exceed total (overpayment not tracked here)
    amount_paid = min(amount_paid, total)
    amount_due  = round(total - amount_paid, 2)

    if amount_paid >= total:
        status = "paid"
    elif amount_paid > 0:
        status = "partial"
    else:
        status = "unpaid"

    invoice_no = next_invoice_number(session)

    customer = _get_customer(session, customer_id) if customer_id else None
    customer_name = customer.name if customer else "Walk-in"

    sale = Sale(
        invoice_number=invoice_no,
        customer_id=customer_id,
        customer_name=customer_name,
        subtotal=subtotal,
        discount_type=discount_type,
        discount_value=float(discount_value),
        discount_amount=discount_amount,
        total=total,
        amount_paid=amount_paid,
        amount_due=amount_due,
        status=status,
        notes=notes,
    )
    session.add(sale)
    session.flush()

    for i in items:
        qty   = float(i["quantity"])
        price = float(i["unit_price"])
        product = _get_product(session, i["product_id"])

        session.add(SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            product_name=product.name,
            quantity=qty,
            unit_price=price,
            line_total=round(qty * price, 2)
        ))

        # Deduct stock — floor at 0, never negative
        product.current_stock = round(max(product.current_stock - qty, 0.0), 4)
        product.updated_at = datetime.now()

        session.add(StockMovement(
            product_id=product.id,
            movement_type="OUT",
            quantity=qty,
            note=f"Sale {invoice_no}",
            sale_id=sale.id
        ))

    if customer and amount_due > 0:
        customer.due_balance = round(customer.due_balance + amount_due, 2)

    session.commit()
    return sale


# ---------------------------------------------------------------------------
# Returns
# ---------------------------------------------------------------------------

def process_return(session, product_id, quantity, reason, description,
                   unit_price, restock, refund_method,
                   customer_id=None, sale_id=None):
    from models import ReturnItem, next_return_number

    qty = float(quantity)
    if qty <= 0:
        raise ValueError("Return quantity must be greater than zero.")

    product = _get_product(session, product_id)
    if not product:
        raise ValueError("Product not found.")

    refund_total = round(qty * float(unit_price), 2)
    return_no    = next_return_number(session)

    customer      = _get_customer(session, customer_id) if customer_id else None
    customer_name = customer.name if customer else "Walk-in"

    ret = ReturnItem(
        return_number=return_no,
        sale_id=sale_id,
        customer_id=customer_id,
        customer_name=customer_name,
        product_id=product_id,
        product_name=product.name,
        quantity=qty,
        unit_price=float(unit_price),
        refund_total=refund_total,
        reason=reason,
        description=description,
        restock=restock,
        refund_method=refund_method,
    )
    session.add(ret)

    if restock:
        product.current_stock = round(product.current_stock + qty, 4)
        product.updated_at = datetime.now()
        session.add(StockMovement(
            product_id=product_id,
            movement_type="IN",
            quantity=qty,
            note=f"Return {return_no} — {reason}"
        ))

    # Credit to Account: reduce the customer's due balance (they owe less)
    if refund_method == "Credit to Account" and customer and refund_total > 0:
        customer.due_balance = round(max(customer.due_balance - refund_total, 0.0), 2)

    session.commit()
    return ret


def get_all_returns(session, query=""):
    from models import ReturnItem
    q = session.query(ReturnItem)
    if query:
        like = f"%{query}%"
        q = q.filter(
            ReturnItem.product_name.ilike(like)  |
            ReturnItem.customer_name.ilike(like) |
            ReturnItem.return_number.ilike(like) |
            ReturnItem.reason.ilike(like)
        )
    return q.order_by(ReturnItem.created_at.desc()).all()


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def daily_sales_report(session, target_date=None):
    if target_date is None:
        target_date = date.today()
    start = datetime.combine(target_date, datetime.min.time())
    end   = datetime.combine(target_date, datetime.max.time())
    sales = session.query(Sale).filter(Sale.date.between(start, end)).all()
    return {
        "date":            target_date,
        "count":           len(sales),
        "total_revenue":   sum(s.total       for s in sales),
        "total_collected": sum(s.amount_paid for s in sales),
        "total_due":       sum(s.amount_due  for s in sales),
        "sales":           sales,
    }


def monthly_sales_report(session, year, month):
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    start = datetime(year, month, 1)
    end   = datetime(year, month, last_day, 23, 59, 59)
    sales = session.query(Sale).filter(Sale.date.between(start, end)).all()

    total_cost   = 0.0
    product_qty  = {}
    for s in sales:
        for si in s.sale_items:
            cost = si.product.cost_price if si.product else 0.0
            total_cost += si.quantity * cost
            product_qty[si.product_name] = (
                product_qty.get(si.product_name, 0) + si.quantity
            )

    revenue     = sum(s.total for s in sales)
    top_products = sorted(product_qty.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "year":            year,
        "month":           month,
        "count":           len(sales),
        "total_revenue":   revenue,
        "total_cost":      total_cost,
        "gross_profit":    round(revenue - total_cost, 2),
        "total_collected": sum(s.amount_paid for s in sales),
        "total_due":       sum(s.amount_due  for s in sales),
        "top_products":    top_products,
        "sales":           sales,
    }


def get_customer_ledger(session, customer_id):
    customer = _get_customer(session, customer_id)
    sales    = (session.query(Sale)
                .filter_by(customer_id=customer_id)
                .order_by(Sale.date.desc()).all())
    payments = (session.query(Payment)
                .filter_by(customer_id=customer_id)
                .order_by(Payment.created_at.desc()).all())
    return {"customer": customer, "sales": sales, "payments": payments}


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def backup_database(db_path: str) -> str:
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest  = os.path.join(backup_dir, f"shop_{stamp}.db")
    shutil.copy2(db_path, dest)
    # Keep only the 30 most recent backups
    files = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".db")],
        reverse=True
    )
    for old in files[30:]:
        os.remove(os.path.join(backup_dir, old))
    return dest
