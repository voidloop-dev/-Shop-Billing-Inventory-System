"""
Customers Screen — list, add, edit customers, view ledgers, record payments.
"""

import customtkinter as ctk
import tkinter as tk
from theme import (
    COLORS, FONT, Card, AppButton, AppEntry, AppLabel,
    Divider, IconButton, ModalDialog, StatusBadge,
    show_error, show_info, confirm_dialog
)
import business


class CustomersScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        AppLabel(top, "Customers", style="heading_lg").pack(side="left")
        AppButton(top, "+ Add Customer", command=self._open_add, width=140, height=38).pack(side="right")

        # Search
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        AppEntry(top, placeholder="Search name or phone…",
                 textvariable=self.search_var, width=280).pack(side="right", padx=(0, 12))

        # List
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 16))

        # Header
        hdr = ctk.CTkFrame(self.list_frame, fg_color="#F1F3F5", corner_radius=8)
        hdr.pack(fill="x", pady=(0, 4))
        for text, width in [("Name", 220), ("Phone", 140), ("Default Disc.", 120),
                             ("Total Due", 130), ("", 200)]:
            ctk.CTkLabel(hdr, text=text, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"],
                         width=width, anchor="w").pack(side="left", padx=8, pady=8)
        self._hdr = hdr

    def refresh(self, *_):
        # Remove old rows but keep header
        for w in self.list_frame.winfo_children():
            if w is not self._hdr:
                w.destroy()

        query = self.search_var.get().strip()
        customers = business.search_customers(self.session, query)
        currency = business.get_setting(self.session, "currency", "Rs.")

        if not customers:
            ctk.CTkLabel(self.list_frame, text="No customers found.",
                         font=FONT["body"], text_color=COLORS["text_muted"]).pack(pady=40)
            return

        for c in customers:
            self._add_row(c, currency)

    def _add_row(self, c, currency):
        bg = COLORS["bg_card"]
        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=8)
        row.pack(fill="x", pady=2)
        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=COLORS["bg_hover"]))
        row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=bg))

        due_color = COLORS["warning"] if c.due_balance > 0 else COLORS["text_muted"]

        for text, width, color in [
            (c.name, 220, COLORS["text_primary"]),
            (c.phone or "—", 140, COLORS["text_secondary"]),
            (f"{c.default_discount:.0f}%", 120, COLORS["text_secondary"]),
            (f"{currency} {c.due_balance:,.0f}", 130, due_color),
        ]:
            ctk.CTkLabel(row, text=text, font=FONT["body"],
                         text_color=color, width=width, anchor="w").pack(
                side="left", padx=8, pady=10)

        actions = ctk.CTkFrame(row, fg_color="transparent", width=200)
        actions.pack(side="left", padx=8, pady=4)
        IconButton(actions, "Ledger", command=lambda cid=c.id: self._open_ledger(cid),
                   style="primary").pack(side="left", padx=(0, 4))
        if c.due_balance > 0:
            IconButton(actions, "Pay Due", command=lambda cid=c.id: self._open_payment(cid),
                       style="success").pack(side="left", padx=(0, 4))
        IconButton(actions, "Edit", command=lambda cid=c.id: self._open_edit(cid),
                   style="ghost").pack(side="left")

    def _open_add(self):
        CustomerDialog(self, self.session, on_save=self.refresh)

    def _open_edit(self, cid):
        c = self.session.query(business.Customer).get(cid)
        CustomerDialog(self, self.session, customer=c, on_save=self.refresh)

    def _open_ledger(self, cid):
        CustomerLedger(self, self.session, cid, on_payment=self.refresh)

    def _open_payment(self, cid):
        c = self.session.query(business.Customer).get(cid)
        PaymentDialog(self, self.session, c, on_save=self.refresh)


# ---------------------------------------------------------------------------
# Add / Edit Customer Dialog
# ---------------------------------------------------------------------------

class CustomerDialog(ModalDialog):
    def __init__(self, parent, session, customer=None, on_save=None):
        super().__init__(parent, "Edit Customer" if customer else "Add Customer",
                         width=480, height=420)
        self.session = session
        self.customer = customer
        self.on_save = on_save
        self._build()
        if customer:
            self._populate()

    def _build(self):
        self._header("Customer Details")
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        def row(label, var, placeholder=""):
            ctk.CTkLabel(body, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(10, 2))
            AppEntry(body, placeholder=placeholder, textvariable=var, width=420).pack(anchor="w")

        self.v_name    = tk.StringVar()
        self.v_phone   = tk.StringVar()
        self.v_address = tk.StringVar()
        self.v_disc    = tk.StringVar(value="0")

        row("Name *", self.v_name, "Customer name")
        row("Phone", self.v_phone, "Phone number")
        row("Address (optional)", self.v_address, "Address")
        row("Default Discount (%)", self.v_disc, "0")

        self._footer(on_cancel=self.destroy, on_confirm=self._save, confirm_text="Save Customer")

    def _populate(self):
        c = self.customer
        self.v_name.set(c.name)
        self.v_phone.set(c.phone or "")
        self.v_address.set(c.address or "")
        self.v_disc.set(str(c.default_discount))

    def _save(self):
        name = self.v_name.get().strip()
        if not name:
            show_error(self, "Customer name is required.")
            return
        try:
            disc = float(self.v_disc.get() or 0)
        except ValueError:
            show_error(self, "Discount must be a number.")
            return

        kwargs = dict(name=name, phone=self.v_phone.get().strip(),
                      address=self.v_address.get().strip(), default_discount=disc)
        if self.customer:
            business.update_customer(self.session, self.customer.id, **kwargs)
        else:
            business.add_customer(self.session, **kwargs)

        if self.on_save:
            self.on_save()
        self.destroy()


# ---------------------------------------------------------------------------
# Customer Ledger
# ---------------------------------------------------------------------------

class CustomerLedger(ModalDialog):
    def __init__(self, parent, session, customer_id, on_payment=None):
        super().__init__(parent, "Customer Ledger", width=700, height=600)
        self.session = session
        self.customer_id = customer_id
        self.on_payment = on_payment
        self._build()

    def _build(self):
        data = business.get_customer_ledger(self.session, self.customer_id)
        c = data["customer"]
        currency = business.get_setting(self.session, "currency", "Rs.")

        self._header(f"Ledger — {c.name}")

        # Summary strip
        summary = ctk.CTkFrame(self, fg_color="#F1F3F5", corner_radius=0, height=60)
        summary.pack(fill="x")
        summary.pack_propagate(False)
        for label, value, color in [
            ("Phone", c.phone or "—", COLORS["text_secondary"]),
            ("Default Discount", f"{c.default_discount:.0f}%", COLORS["text_secondary"]),
            ("Total Due Balance", f"{currency} {c.due_balance:,.0f}",
             COLORS["warning"] if c.due_balance > 0 else COLORS["success"]),
        ]:
            col = ctk.CTkFrame(summary, fg_color="transparent")
            col.pack(side="left", padx=20)
            ctk.CTkLabel(col, text=label, font=FONT["label"],
                         text_color=COLORS["text_muted"]).pack(anchor="w")
            ctk.CTkLabel(col, text=value, font=FONT["body"],
                         text_color=color).pack(anchor="w")

        if c.due_balance > 0:
            AppButton(summary, "Record Payment",
                      command=lambda: self._record_payment(c),
                      style="success", width=150, height=34).pack(side="right", padx=20)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        # Sales
        ctk.CTkLabel(scroll, text="Invoices", font=FONT["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 8))
        if data["sales"]:
            for s in data["sales"]:
                row = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=8)
                row.pack(fill="x", pady=2)
                date_str = s.date.strftime("%d %b %Y")
                for text, width, color in [
                    (s.invoice_number, 130, COLORS["text_accent"]),
                    (date_str, 100, COLORS["text_secondary"]),
                    (f"Total: {currency} {s.total:,.0f}", 150, COLORS["text_primary"]),
                    (f"Paid: {currency} {s.amount_paid:,.0f}", 150, COLORS["success"]),
                    (f"Due: {currency} {s.amount_due:,.0f}", 130, COLORS["warning"]),
                ]:
                    ctk.CTkLabel(row, text=text, font=FONT["body_sm"],
                                 text_color=color, width=width, anchor="w").pack(
                        side="left", padx=8, pady=8)
                StatusBadge(row, s.status).pack(side="left", padx=4)
        else:
            ctk.CTkLabel(scroll, text="No invoices yet.",
                         font=FONT["body"], text_color=COLORS["text_muted"]).pack(pady=8)

        Divider(scroll).pack(fill="x", pady=12)

        # Payments
        ctk.CTkLabel(scroll, text="Payments Received", font=FONT["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 8))
        if data["payments"]:
            for p in data["payments"]:
                row = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=8)
                row.pack(fill="x", pady=2)
                date_str = p.created_at.strftime("%d %b %Y %H:%M")
                for text, width, color in [
                    (date_str, 180, COLORS["text_secondary"]),
                    (f"{currency} {p.amount:,.0f}", 140, COLORS["success"]),
                    (p.note or "—", 300, COLORS["text_muted"]),
                ]:
                    ctk.CTkLabel(row, text=text, font=FONT["body_sm"],
                                 text_color=color, width=width, anchor="w").pack(
                        side="left", padx=8, pady=8)
        else:
            ctk.CTkLabel(scroll, text="No payments recorded yet.",
                         font=FONT["body"], text_color=COLORS["text_muted"]).pack(pady=8)

        AppButton(self, "Close", command=self.destroy, style="ghost",
                  width=100, height=36).pack(pady=(0, 12))

    def _record_payment(self, customer):
        def after_payment():
            if self.on_payment:
                self.on_payment()
            # Rebuild ledger with fresh data instead of closing it
            try:
                for w in self.winfo_children():
                    w.destroy()
                self._build()
            except Exception:
                pass
        PaymentDialog(self, self.session, customer, on_save=after_payment)


# ---------------------------------------------------------------------------
# Record Payment Dialog
# ---------------------------------------------------------------------------

class PaymentDialog(ModalDialog):
    def __init__(self, parent, session, customer, on_save=None):
        super().__init__(parent, "Record Payment", width=420, height=340)
        self.session = session
        self.customer = customer
        self.on_save = on_save
        self._build()

    def _build(self):
        self._header(f"Payment from {self.customer.name}")
        currency = business.get_setting(self.session, "currency", "Rs.")
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(body,
                     text=f"Outstanding due: {currency} {self.customer.due_balance:,.0f}",
                     font=FONT["body_lg"], text_color=COLORS["warning"]).pack(anchor="w", pady=(0, 16))

        ctk.CTkLabel(body, text="Amount Received (Rs.)", font=FONT["label_bold"],
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(0, 4))
        self.v_amount = tk.StringVar(value=str(self.customer.due_balance))
        AppEntry(body, placeholder="Amount", textvariable=self.v_amount, width=370).pack(anchor="w")

        ctk.CTkLabel(body, text="Note (optional)", font=FONT["label_bold"],
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(12, 4))
        self.v_note = tk.StringVar()
        AppEntry(body, placeholder="e.g. Cash payment", textvariable=self.v_note,
                 width=370).pack(anchor="w")

        self._footer(on_cancel=self.destroy, on_confirm=self._save,
                     confirm_text="Record Payment", confirm_style="success")

    def _save(self):
        try:
            amount = float(self.v_amount.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            show_error(self, "Enter a valid payment amount.")
            return

        try:
            business.record_payment(self.session, self.customer.id,
                                    amount, note=self.v_note.get().strip())
        except Exception as e:
            show_error(self, str(e))
            return

        if self.on_save:
            self.on_save()
        show_info(self, f"Payment of Rs. {amount:,.0f} recorded.", "Payment Saved")
        self.destroy()
