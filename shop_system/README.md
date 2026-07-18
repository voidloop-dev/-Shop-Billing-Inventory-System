# 🏪 Shop Billing & Inventory System

A fully offline, desktop-based billing and inventory management system built for small retail shops. Designed for day-to-day counter use — fast invoicing, stock tracking, customer due management, and return processing. No internet required. No server. No subscription.

> Built as a real-world project while learning Python. Open source, free to use, and simple enough for a non-technical person to operate daily.

---

## 📸 What It Looks Like

**Layout:** Dark navy sidebar navigation + warm white content area — the same pattern used by QuickBooks, Zoho Books, and Shopify POS. Readable all day without eye strain.

**Screens:** Login → Dashboard → New Sale → Products → Stock In → Stock Check → Returns → Customers → Reports → Settings

---

## ✅ Features (v1.0)

### 🧾 Billing / New Sale
- Search products by typing just 1–2 letters — results appear instantly as a dropdown
- Add multiple products to a bill with editable quantity and price per line
- Customer default discount auto-applies when a known customer is selected
- Manual discount override — choose **% percentage** or **flat Rs. amount** — live hint shows the equivalent in the other unit (e.g. "= Rs. 450 off")
- "Set Full Amount" button auto-fills the received amount
- Partial payment tracking — remaining balance automatically added to customer's due account
- Invoice status: **Paid / Partial / Unpaid** — calculated automatically
- Save only, or Save + generate and open a PDF invoice for printing
- All stock deductions happen automatically on sale completion

### 📦 Products
- Full product catalog with name, category, unit, size (inch / mm / feet / meter / N/A), cost price, selling price, current stock, and low-stock threshold
- Size field is two-part: value + unit — handles fractional sizes like ½", ¾" correctly as text
- Add / edit / deactivate products (deactivate keeps historical invoice data intact)
- Low-stock flag shown on product list and dashboard alert

### 📥 Stock In (Restocking)
- Select product, enter quantity received, optional supplier note
- Stock increases immediately, logged as a full audit trail (not just a running number)
- Recent stock-ins shown live on the right panel

### 🔍 Stock Check
- Dedicated screen for "does this product exist?" — what counter staff use when a customer asks
- Big prominent search bar, triggers from first character typed
- Shows: product name, category, size, selling price, current stock, availability status
- Color-coded rows: green (available), amber (low stock), red (out of stock)
- Filter buttons: All / In Stock / Low Stock / Out of Stock
- "Add to Bill →" shortcut jumps straight to billing

### ↩️ Returns
- Process returned items with: original invoice lookup (optional), product search, quantity, refund price per unit, live refund total
- **Reason dropdown:** Defective/Damaged, Wrong Item, Customer Changed Mind, Excess Quantity, Quality Not Acceptable, Other
- **Detailed description** text field — required, explains what exactly is wrong
- Toggle: restock the item back into inventory or not
- **Refund method:** Cash or Credit to Account (automatically reduces customer's due balance)
- Full returns history with stats panel showing total refunds, quantities, and breakdown by reason

### 👥 Customers
- Customer list with name, phone, address, default discount %, running due balance
- Full ledger per customer: all invoices + all payments in one view
- Record payments against due balance — balance updates instantly
- "Pay Due" button visible directly on the list when a customer has a balance

### 📊 Reports
- **Daily report:** pick any date, see invoice count, revenue, collected cash, outstanding due
- **Monthly report:** total revenue, cost of goods, gross profit, top 10 products by quantity sold, all invoices
- Profit calculation uses cost price vs selling price — real numbers, not just revenue

### ⚙️ Settings
- Shop name, address, phone — printed on every invoice
- Change admin password
- Manual backup trigger (auto-backup also runs on every app close)

### 🔒 Security & Reliability
- Single admin password at startup — hashed with SHA-256, never stored in plain text
- Input validation everywhere — no crashes from empty fields or bad numbers
- Stock floors at zero, never goes negative — with a clear warning if overselling
- Auto-backup on close — dated copies saved to `backups/` folder, keeps last 30
- Crash handler — unexpected errors logged to `error.log`, shown as a friendly message
- All historical invoice data preserved even if products are deactivated

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Language** | Python 3.10+ | Learner-friendly, powerful, huge ecosystem |
| **GUI Framework** | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Native desktop app — no browser, no server, no launch failures |
| **Database** | SQLite (via [SQLAlchemy](https://www.sqlalchemy.org/)) | Single `.db` file, zero setup, no separate database server needed |
| **ORM** | SQLAlchemy 2.x | Clean data access layer, prevents raw SQL bugs |
| **PDF Invoices** | [ReportLab](https://www.reportlab.com/) | Generates printable A4 invoices, works with any printer |
| **Packaging** | [PyInstaller](https://pyinstaller.org/) | Compiles to a single `.exe` — no Python needed on end-user's machine |
| **Password Hashing** | Python `hashlib` (SHA-256) | Secure local password storage without external dependencies |

### Architecture
Single-process desktop application. GUI, business logic, and database all run in one process on one machine. No client-server split, no network calls, no external services. The entire shop's data is one file: `shop.db`.

```
main.py              ← Entry point, window, startup
├── screen_login.py  ← Password screen
├── main_app.py      ← Sidebar navigation shell
│
├── screen_dashboard.py   ← Home / daily summary
├── screen_billing.py     ← New Sale (core screen)
├── screen_products.py    ← Product catalog
├── screen_stock_in.py    ← Restock
├── screen_stock_check.py ← Availability search
├── screen_returns.py     ← Return processing
├── screen_customers.py   ← Customer ledger
├── screen_reports.py     ← Daily + monthly reports
├── screen_settings.py    ← Shop info, password
│
├── business.py      ← All logic: billing, stock, discounts, returns
├── models.py        ← Database schema (SQLAlchemy models)
├── theme.py         ← Colors, fonts, shared widgets
└── invoice_pdf.py   ← PDF generation
```

**Key design principle:** `business.py` has zero GUI code. All money math, stock deductions, discount calculations, and database writes live there and can be tested independently of the interface.

---

## 🎨 Theme Evolution

### v1 — Dark Blue (Abandoned)
The first theme used a deep dark palette inspired by developer tools like Linear and Vercel:
- Background: `#0D0F12` (near black)
- Cards: `#181B22`
- Accent: `#4F6BED` (indigo blue)

**Problem:** Looked good in screenshots but was difficult to read in real use — dark text on dark cards, blue accent blending into dark backgrounds. Fine for a code editor, wrong for a billing app used under shop lighting all day.

### v2 — Light Content + Dark Navy Sidebar (Current)
After researching QuickBooks, Zoho Books, Shopify POS, and Tally Prime — every major billing tool uses the same pattern: **dark sidebar for navigation, white/light content for data.**

The reason is practical: counter staff stare at invoices and product lists for hours. Black text on white is simply faster to read and causes less eye strain than the reverse.

| Element | Color | Reference |
|---|---|---|
| Sidebar | Deep navy `#1B2A3B` | QuickBooks / Zoho Books |
| Content background | Warm grey `#F4F5F7` | Not cold pure white |
| Cards | White `#FFFFFF` | Clean data panels |
| Accent | Forest green `#1A7F5A` | Zoho Books / Tally Prime |
| Warning | Amber `#B45309` | Low stock, due balance |
| Danger | Deep red `#B91C1C` | Errors, unpaid, delete |
| Text | Near-black `#111827` | Maximum contrast |

---

## 🐛 Bugs Found and Fixed

### Critical — Would crash or give wrong data

| Bug | Where | What happened | Fix |
|---|---|---|---|
| **Product selection wiped on "Add"** | Billing screen | Selecting a product from the dropdown filled the search box text, which triggered the `trace_add("write")` callback, which reset `_selected_product = None` before "Add" was clicked | Added `_suppress_search` flag — suppresses the trace when code (not user) sets the search text |
| **Same bug in Returns screen** | Returns dialog | Identical root cause — picking a product in the return dialog cleared the selection | Same suppress-flag fix applied |
| **`_linked_sale` not initialized** | Returns dialog | `getattr(self, "_linked_sale", None)` was used as a workaround for an attribute never set in `__init__` — fragile and confusing | Initialized to `None` properly in `__init__` |
| **Deprecated `session.query().get()`** | `business.py`, `screen_products.py` | SQLAlchemy 2.x removed `.get()` on Query objects — causes runtime errors | Replaced all with `.filter_by(id=...).first()` |
| **Double-destroy crash in Customer Ledger** | `screen_customers.py` | After recording a payment, a lambda called `self.destroy()` then `self.on_payment()` — if the dialog was already closed, raised TclError | Replaced with `after_payment()` function that rebuilds the ledger in-place instead |
| **Duplicate variable definitions in PDF** | `invoice_pdf.py` | `col_widths` and `items_header` were defined twice — first definition was dead code silently overwritten | Removed the dead first block |
| **Missing color keys at runtime** | All screens | `COLORS["bg_dark"]` and `COLORS["accent_light"]` were referenced everywhere after the theme was rewritten, causing KeyError on launch | Added backward-compat aliases in `theme.py` |

### Logic bugs — Wrong results silently

| Bug | What happened | Fix |
|---|---|---|
| **Overpayment not caught** | Entering more than the total created a negative `amount_due` | Capped `amount_paid` at `total` before computing due |
| **Discount % over 100% allowed** | Entering 150% discount produced a negative total | Clamped percentage to 0–100 range |
| **Low stock threshold off-by-one** | Items with stock exactly equal to threshold showed as "Low Stock" | Changed `<=` to `<` — at the threshold is ok, below it is low |
| **Float accumulation drift** | Repeated stock additions/subtractions drifted (e.g. 10.000000001) | All stock values now rounded to 4 decimal places |
| **Overpayment in `record_payment`** | Paying more than due balance didn't error | Added check: payment silently capped at actual due balance |
| **Daily report called twice** | Dashboard loaded `daily_sales_report()` twice per visit — two DB queries for same data | Deduplicated — result reused |
| **Monthly report month dropdown mismatch** | `month_var` initialized to `"7"` but OptionMenu expects `"7 - Jul"` — displayed blank on first open | Initialized to the full label string |
| **Unused variable `actual_deduct`** | Computed in `create_sale` but never used | Removed |

---

## 🧩 Challenges Faced

**1. The search-trace loop**
The trickiest bug. In Tkinter, `StringVar.trace_add("write", callback)` fires every time the variable changes — including when your own code changes it. Selecting a product filled the entry box, which fired the search callback, which cleared the selection. The solution (a suppress flag) is simple but the bug is completely invisible until you test the exact click sequence.

**2. SQLAlchemy version gap**
The project started with `.get()` calls which are the old SQLAlchemy 1.x API. SQLAlchemy 2.x deprecated and removed it. Since CustomTkinter's dependencies pull in a newer SQLAlchemy, this would silently install the version that breaks the code. Fixed by migrating all lookups to the new `.filter_by().first()` pattern.

**3. Full dark theme readability**
Spent time building a full dark theme before realizing it was the wrong choice for this use case. A billing app used under fluorescent shop lighting needs maximum text contrast. Dark themes work for developers staring at code in dim rooms — not for counter staff reading Rs. amounts quickly under bright lights. Researching actual competitor software (QuickBooks, Zoho, Tally) made this obvious.

**4. Keeping business logic separate**
Discipline to never put billing calculations inside screen files paid off during bug fixing. When the discount logic needed fixing, it was in one place (`business.py`) and the fix immediately applied everywhere — billing screen, returns screen, and reports all use the same function.

**5. Offline-first data integrity**
No cloud, no sync, no recovery service. If `shop.db` corrupts, data is gone. The auto-backup-on-close system (keeping 30 dated copies) is the only safety net. The README explicitly instructs copying to a USB drive periodically because that habit is more reliable than any automated cloud system for a non-technical user.

---

## 🗺️ Roadmap — What Comes Next (Phase 2)

- [ ] **Online store** — web-based front-end (separate project, separate tech stack)
- [ ] **Multi-computer sync** — for shops with more than one counter
- [ ] **Receipt printer support** — thermal printer via ESC/POS protocol
- [ ] **GST / Tax support** — tax-inclusive and tax-exclusive pricing
- [ ] **Barcode scanning** — scan products into billing instead of typing
- [ ] **Export reports** — PDF and Excel export for monthly reports
- [ ] **Product images** — attach photo to each product
- [ ] **Supplier management** — track which supplier each product comes from
- [ ] **Purchase orders** — formal restock orders with expected delivery dates
- [ ] **Multiple price tiers** — wholesale vs retail pricing per customer type

---

## 🚀 How to Run

### Requirements
- Windows 10 or 11
- Python 3.10 or higher → [python.org/downloads](https://python.org/downloads)
- ✅ During Python install: check **"Add Python to PATH"**

### Step 1 — Clone or download

```bash
git clone https://github.com/yourusername/shop-billing-system.git
cd shop-billing-system
```

Or download the ZIP and extract it.

### Step 2 — Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

You'll see `(venv)` at the start of your terminal line.

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs: `customtkinter`, `sqlalchemy`, `reportlab`, `pyinstaller`

### Step 4 — Run

```bash
python main.py
```

Or double-click **`RUN_APP.bat`**

### First time setup
1. Set your admin password (minimum 4 characters)
2. Go to **Settings** → enter shop name, address, phone number
3. Go to **Products** → add your products with prices and opening stock
4. Start billing with **New Sale**

---

## 📦 Package as .exe (for non-technical users)

To give to someone who doesn't have Python installed:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ShopSystem main.py
```

The `.exe` appears in the `dist/` folder. Copy these alongside it:
- `shop.db` (if you want to transfer existing data)
- `backups/` folder
- `invoices/` folder

---

## 📁 File Structure

```
shop-billing-system/
│
├── main.py                 ← Entry point — run this
├── main_app.py             ← Sidebar shell + screen navigation
├── models.py               ← Database schema (8 tables)
├── business.py             ← All business logic — billing, stock, discounts
├── theme.py                ← Color palette, fonts, shared widgets
├── invoice_pdf.py          ← PDF invoice generator
│
├── screen_login.py         ← Password screen
├── screen_dashboard.py     ← Home screen with daily summary
├── screen_billing.py       ← New Sale — the core daily screen
├── screen_products.py      ← Product catalog management
├── screen_stock_in.py      ← Restock / stock-in
├── screen_stock_check.py   ← Quick availability search
├── screen_returns.py       ← Return item processing
├── screen_customers.py     ← Customer list + ledger + payments
├── screen_reports.py       ← Daily and monthly reports
├── screen_settings.py      ← Shop info and password
│
├── requirements.txt        ← Python dependencies
├── RUN_APP.bat             ← Windows double-click launcher
├── assets/                 ← (reserved for icons/images in future)
│
├── shop.db                 ← Your data (auto-created on first run)
├── backups/                ← Auto-backups (auto-created)
├── invoices/               ← Generated PDFs (auto-created)
└── error.log               ← Crash logs (auto-created if needed)
```

---

## 🗃️ Database Schema

| Table | Purpose |
|---|---|
| `products` | Catalog — name, size, prices, stock, threshold |
| `stock_movements` | Full audit trail of every stock change (IN/OUT) |
| `customers` | Customer profiles with default discount and due balance |
| `sales` | Every invoice — totals, discount, status, customer |
| `sale_items` | Line items within each invoice (price snapshot at time of sale) |
| `payments` | Customer payments against their due balance |
| `return_items` | Returned products with reason, description, refund |
| `settings` | Shop info, password hash, invoice counter |

Stock and customer balances are derived from movement/payment logs — not just a single number — so there's always a full audit trail and nothing silently gets out of sync.

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Built With

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) by Tom Schimansky
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [ReportLab](https://www.reportlab.com/)

---

*Built as a learning project — Python, desktop GUIs, databases, and real-world software design all in one.*
