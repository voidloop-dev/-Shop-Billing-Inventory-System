"""
Database models for the Offline Shop Billing & Inventory System.
Uses SQLAlchemy with SQLite — single file, zero server, zero setup.
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    ForeignKey, Text, Boolean, Enum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class Product(Base):
    __tablename__ = "products"

    id              = Column(Integer, primary_key=True)
    name            = Column(String(200), nullable=False)
    category        = Column(String(100), default="General")
    unit            = Column(String(50), default="piece")   # piece / box / meter / ...
    size_value      = Column(String(50), default="")        # "1/2", "3/4", "1", etc.
    size_unit       = Column(String(20), default="N/A")     # inch / mm / feet / meter / N/A
    cost_price      = Column(Float, default=0.0)
    selling_price   = Column(Float, default=0.0)
    current_stock   = Column(Float, default=0.0)
    low_stock_threshold = Column(Float, default=5.0)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.now)
    updated_at      = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    stock_movements = relationship("StockMovement", back_populates="product")
    sale_items      = relationship("SaleItem", back_populates="product")

    @property
    def display_size(self):
        if self.size_unit == "N/A" or not self.size_value:
            return ""
        return f"{self.size_value} {self.size_unit}"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.low_stock_threshold

    def __repr__(self):
        return f"<Product {self.name}>"


# ---------------------------------------------------------------------------
# Stock Movements  (IN = restock, OUT = sale)
# ---------------------------------------------------------------------------

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id          = Column(Integer, primary_key=True)
    product_id  = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(10), nullable=False)   # "IN" or "OUT"
    quantity    = Column(Float, nullable=False)
    note        = Column(Text, default="")
    created_at  = Column(DateTime, default=datetime.now)
    sale_id     = Column(Integer, ForeignKey("sales.id"), nullable=True)

    product     = relationship("Product", back_populates="stock_movements")
    sale        = relationship("Sale", back_populates="stock_movements")

    def __repr__(self):
        return f"<StockMovement {self.movement_type} {self.quantity} of product {self.product_id}>"


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

class Customer(Base):
    __tablename__ = "customers"

    id               = Column(Integer, primary_key=True)
    name             = Column(String(200), nullable=False)
    phone            = Column(String(50), default="")
    address          = Column(Text, default="")
    default_discount = Column(Float, default=0.0)   # percentage
    due_balance      = Column(Float, default=0.0)   # running total owed
    created_at       = Column(DateTime, default=datetime.now)

    sales    = relationship("Sale", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.name}>"


# ---------------------------------------------------------------------------
# Sales / Invoices
# ---------------------------------------------------------------------------

class Sale(Base):
    __tablename__ = "sales"

    id              = Column(Integer, primary_key=True)
    invoice_number  = Column(String(50), unique=True, nullable=False)
    customer_id     = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name   = Column(String(200), default="Walk-in")   # snapshot for walk-ins
    date            = Column(DateTime, default=datetime.now)
    subtotal        = Column(Float, default=0.0)
    discount_type   = Column(String(10), default="percent")    # "percent" or "flat"
    discount_value  = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)               # computed
    total           = Column(Float, default=0.0)
    amount_paid     = Column(Float, default=0.0)
    amount_due      = Column(Float, default=0.0)
    status          = Column(String(20), default="unpaid")     # paid / partial / unpaid
    notes           = Column(Text, default="")

    customer        = relationship("Customer", back_populates="sales")
    sale_items      = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments        = relationship("Payment", back_populates="sale")
    stock_movements = relationship("StockMovement", back_populates="sale")

    def __repr__(self):
        return f"<Sale {self.invoice_number}>"


class SaleItem(Base):
    __tablename__ = "sale_items"

    id          = Column(Integer, primary_key=True)
    sale_id     = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id  = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)   # snapshot
    quantity    = Column(Float, nullable=False)
    unit_price  = Column(Float, nullable=False)           # price at time of sale
    line_total  = Column(Float, nullable=False)

    sale        = relationship("Sale", back_populates="sale_items")
    product     = relationship("Product", back_populates="sale_items")

    def __repr__(self):
        return f"<SaleItem {self.product_name} x{self.quantity}>"


# ---------------------------------------------------------------------------
# Payments (customer paying off their due balance)
# ---------------------------------------------------------------------------

class Payment(Base):
    __tablename__ = "payments"

    id          = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    sale_id     = Column(Integer, ForeignKey("sales.id"), nullable=True)
    amount      = Column(Float, nullable=False)
    note        = Column(Text, default="")
    created_at  = Column(DateTime, default=datetime.now)

    customer    = relationship("Customer", back_populates="payments")
    sale        = relationship("Sale", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.amount} from customer {self.customer_id}>"


# ---------------------------------------------------------------------------
# Return Items
# ---------------------------------------------------------------------------

RETURN_REASONS = [
    "Defective / Damaged",
    "Wrong Item Delivered",
    "Customer Changed Mind",
    "Excess Quantity",
    "Quality Not Acceptable",
    "Other",
]

class ReturnItem(Base):
    __tablename__ = "return_items"

    id             = Column(Integer, primary_key=True)
    return_number  = Column(String(50), unique=True, nullable=False)
    sale_id        = Column(Integer, ForeignKey("sales.id"), nullable=True)   # original invoice (optional)
    customer_id    = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name  = Column(String(200), default="Walk-in")
    product_id     = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name   = Column(String(200), nullable=False)   # snapshot
    quantity       = Column(Float, nullable=False)
    unit_price     = Column(Float, default=0.0)            # refund value per unit
    refund_total   = Column(Float, default=0.0)            # computed
    reason         = Column(String(100), default="Other")
    description    = Column(Text, default="")              # detailed description
    restock        = Column(Boolean, default=True)         # add back to stock?
    refund_method  = Column(String(50), default="Cash")    # Cash / Credit to account
    created_at     = Column(DateTime, default=datetime.now)

    product  = relationship("Product")
    sale     = relationship("Sale")
    customer = relationship("Customer")

    def __repr__(self):
        return f"<ReturnItem {self.return_number}>"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class Setting(Base):
    __tablename__ = "settings"

    id          = Column(Integer, primary_key=True)
    key         = Column(String(100), unique=True, nullable=False)
    value       = Column(Text, default="")

    def __repr__(self):
        return f"<Setting {self.key}>"


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def get_db_path():
    """Return the absolute path to shop.db, next to the executable or script."""
    if getattr(__import__("sys"), "frozen", False):
        base = os.path.dirname(__import__("sys").executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "shop.db")


def init_db():
    """Create all tables (safe to call on every startup)."""
    db_path = get_db_path()
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed default settings if they don't exist yet
    defaults = {
        "shop_name":    "My Shop",
        "shop_address": "",
        "shop_phone":   "",
        "currency":     "Rs.",
        "password_hash": "",   # empty = no password set yet → first-run setup
        "invoice_counter": "1000",
        "return_counter": "100",
        "low_stock_default": "5",
    }
    for key, val in defaults.items():
        if not session.query(Setting).filter_by(key=key).first():
            session.add(Setting(key=key, value=val))
    session.commit()
    session.close()
    return engine


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


def next_return_number(session):
    """Atomically increment and return the next return number."""
    setting = session.query(Setting).filter_by(key="return_counter").first()
    num = int(setting.value)
    setting.value = str(num + 1)
    session.commit()
    return f"RET-{num:04d}"


def next_invoice_number(session):
    """Atomically increment and return the next invoice number."""
    setting = session.query(Setting).filter_by(key="invoice_counter").first()
    num = int(setting.value)
    setting.value = str(num + 1)
    session.commit()
    return f"INV-{num:05d}"
