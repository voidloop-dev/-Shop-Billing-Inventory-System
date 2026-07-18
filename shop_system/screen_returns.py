"""
Returns Screen — process returned items with reason + description.
Handles restocking and refund method.
"""

import customtkinter as ctk
import tkinter as tk
from theme import (
    COLORS, FONT, Card, AppButton, AppEntry, AppLabel,
    Divider, IconButton, ModalDialog, show_error, show_info
)
import business
from models import RETURN_REASONS


REFUND_METHODS = ["Cash", "Credit to Account"]


class ReturnsScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()
        self._refresh_list()

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        AppLabel(top, "Returns", style="heading_lg").pack(side="left")
        AppButton(top, "+ New Return", command=self._open_new_return,
                  style="danger", width=140, height=38).pack(side="right")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        AppEntry(top, placeholder="Search by product, customer, reason…",
                 textvariable=self.search_var, width=300).pack(side="right", padx=(0, 12))

        # Split: left = list, right = stats
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 16))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, minsize=260)
        main.rowconfigure(0, weight=1)

        # Returns list
        list_card = Card(main)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        hdr = ctk.CTkFrame(list_card, fg_color="#F1F3F5", corner_radius=0)
        hdr.pack(fill="x")
        for text, width in [("Return #", 100), ("Date", 110), ("Product", 170),
                             ("Customer", 140), ("Qty", 55), ("Refund", 100),
                             ("Reason", 150), ("Restock", 65)]:
            ctk.CTkLabel(hdr, text=text, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"],
                         width=width, anchor="w").pack(side="left", padx=6, pady=8)

        self.list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

        # Right panel — stats
        right = ctk.CTkFrame(main, fg_color="transparent", width=260)
        right.grid(row=0, column=1, sticky="nsew")
        right.pack_propagate(False)
        self._right = right
        self._build_stats_panel()

    def _build_stats_panel(self):
        for w in self._right.winfo_children():
            w.destroy()

        from models import ReturnItem
        all_returns = self.session.query(ReturnItem).all()
        currency = business.get_setting(self.session, "currency", "Rs.")

        total_refund = sum(r.refund_total for r in all_returns)
        total_qty    = sum(r.quantity for r in all_returns)
        restocked    = sum(1 for r in all_returns if r.restock)

        # Reason breakdown
        from collections import Counter
        reasons = Counter(r.reason for r in all_returns)

        card = Card(self._right)
        card.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=16)

        AppLabel(inner, "Return Summary", style="heading_sm").pack(anchor="w", pady=(0, 12))

        for label, value, color in [
            ("Total Returns", str(len(all_returns)), COLORS["accent"]),
            ("Items Returned", f"{total_qty:.0f}", COLORS["text_primary"]),
            ("Total Refunded", f"{currency} {total_refund:,.0f}", COLORS["danger"]),
            ("Restocked", str(restocked), COLORS["success"]),
        ]:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=FONT["body_sm"],
                         text_color=COLORS["text_secondary"]).pack(side="left")
            ctk.CTkLabel(row, text=value, font=FONT["label_bold"],
                         text_color=color).pack(side="right")

        if reasons:
            Divider(inner).pack(fill="x", pady=10)
            AppLabel(inner, "By Reason", style="label_bold").pack(anchor="w", pady=(0, 6))
            for reason, count in reasons.most_common():
                row = ctk.CTkFrame(inner, fg_color="transparent")
                row.pack(fill="x", pady=2)
                short = reason[:22] + "…" if len(reason) > 22 else reason
                ctk.CTkLabel(row, text=short, font=FONT["body_sm"],
                             text_color=COLORS["text_secondary"]).pack(side="left")
                ctk.CTkLabel(row, text=str(count), font=FONT["label_bold"],
                             text_color=COLORS["text_primary"]).pack(side="right")

    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        query = self.search_var.get().strip()
        returns = business.get_all_returns(self.session, query)
        currency = business.get_setting(self.session, "currency", "Rs.")

        if not returns:
            ctk.CTkLabel(self.list_frame,
                         text="No returns found.\nUse '+ New Return' to process one.",
                         font=FONT["body"], text_color=COLORS["text_muted"]).pack(pady=40)
            return

        for r in returns:
            self._add_row(r, currency)

        self._build_stats_panel()

    def _add_row(self, r, currency):
        bg = COLORS["bg_card"]
        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=8)
        row.pack(fill="x", pady=2)
        row.bind("<Enter>", lambda e, w=row: w.configure(fg_color=COLORS["bg_hover"]))
        row.bind("<Leave>", lambda e, w=row: w.configure(fg_color=bg))

        date_str = r.created_at.strftime("%d %b %Y")
        restock_txt = "✅ Yes" if r.restock else "❌ No"
        restock_color = COLORS["success"] if r.restock else COLORS["text_muted"]

        for text, width, color in [
            (r.return_number, 100, COLORS["text_accent"]),
            (date_str, 110, COLORS["text_secondary"]),
            (r.product_name[:20], 170, COLORS["text_primary"]),
            (r.customer_name[:18], 140, COLORS["text_secondary"]),
            (f"{r.quantity:.0f}", 55, COLORS["text_primary"]),
            (f"{currency} {r.refund_total:,.0f}", 100, COLORS["danger"]),
            (r.reason[:20], 150, COLORS["text_secondary"]),
            (restock_txt, 65, restock_color),
        ]:
            ctk.CTkLabel(row, text=text, font=FONT["body_sm"],
                         text_color=color, width=width, anchor="w").pack(
                side="left", padx=6, pady=8)

        IconButton(row, "Detail", command=lambda ret=r: self._show_detail(ret),
                   style="ghost").pack(side="left", padx=4)

    def _show_detail(self, r):
        ReturnDetailDialog(self, r, business.get_setting(self.session, "currency", "Rs."))

    def _open_new_return(self):
        NewReturnDialog(self, self.session, on_save=self._refresh_list)


# ---------------------------------------------------------------------------
# New Return Dialog
# ---------------------------------------------------------------------------

class NewReturnDialog(ModalDialog):
    def __init__(self, parent, session, on_save=None):
        super().__init__(parent, "Process Return", width=600, height=640)
        self.session = session
        self.on_save = on_save
        self._selected_product = None
        self._linked_sale = None   # set by _lookup_invoice
        self._suppress_search = False
        self._build()

    def _build(self):
        self._header("Process Return / Refund")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=12)

        currency = business.get_setting(self.session, "currency", "Rs.")

        # ---- Invoice reference (optional) ----
        AppLabel(body, "Original Invoice # (optional)", style="label_bold").pack(anchor="w", pady=(0, 4))
        self.v_invoice = tk.StringVar()
        AppEntry(body, placeholder="e.g. INV-01005  — leave blank if unknown",
                 textvariable=self.v_invoice, width=540).pack(anchor="w")
        AppButton(body, "Look Up Invoice", command=self._lookup_invoice,
                  style="ghost", width=150, height=30).pack(anchor="w", pady=(6, 0))
        self.invoice_info = ctk.CTkLabel(body, text="", font=FONT["body_sm"],
                                          text_color=COLORS["text_secondary"])
        self.invoice_info.pack(anchor="w", pady=(2, 8))

        Divider(body).pack(fill="x", pady=8)

        # ---- Product search ----
        AppLabel(body, "Product Being Returned *", style="label_bold").pack(anchor="w", pady=(0, 4))
        self.v_prod = tk.StringVar()
        self.v_prod.trace_add("write", self._on_prod_search)
        AppEntry(body, placeholder="Type product name to search…",
                 textvariable=self.v_prod, width=540).pack(anchor="w")

        self.dropdown = ctk.CTkScrollableFrame(body, fg_color=COLORS["bg_card"],
                                               corner_radius=8, height=0)
        self.dropdown.pack(fill="x", pady=(4, 0))

        self.prod_info = ctk.CTkLabel(body, text="", font=FONT["body_sm"],
                                       text_color=COLORS["success"])
        self.prod_info.pack(anchor="w", pady=(2, 0))

        # ---- Qty + price row ----
        qp_row = ctk.CTkFrame(body, fg_color="transparent")
        qp_row.pack(fill="x", pady=(12, 0))

        col1 = ctk.CTkFrame(qp_row, fg_color="transparent")
        col1.pack(side="left", padx=(0, 16))
        AppLabel(col1, "Quantity Returned *", style="label_bold").pack(anchor="w", pady=(0, 4))
        self.v_qty = tk.StringVar(value="1")
        AppEntry(col1, placeholder="Qty", textvariable=self.v_qty, width=200).pack(anchor="w")

        col2 = ctk.CTkFrame(qp_row, fg_color="transparent")
        col2.pack(side="left")
        AppLabel(col2, f"Refund Price per Unit ({currency}) *", style="label_bold").pack(anchor="w", pady=(0, 4))
        self.v_price = tk.StringVar(value="0")
        AppEntry(col2, placeholder="0", textvariable=self.v_price, width=200).pack(anchor="w")

        # Live refund total
        self.refund_lbl = ctk.CTkLabel(body, text="Refund Total: Rs. 0",
                                        font=FONT["heading_sm"],
                                        text_color=COLORS["danger"])
        self.refund_lbl.pack(anchor="w", pady=(8, 0))
        self.v_qty.trace_add("write", self._update_refund)
        self.v_price.trace_add("write", self._update_refund)

        Divider(body).pack(fill="x", pady=12)

        # ---- Reason ----
        AppLabel(body, "Reason for Return *", style="label_bold").pack(anchor="w", pady=(0, 4))
        self.v_reason = tk.StringVar(value=RETURN_REASONS[0])
        ctk.CTkOptionMenu(body, values=RETURN_REASONS, variable=self.v_reason,
                          fg_color=COLORS["bg_input"],
                          button_color=COLORS["accent"],
                          dropdown_fg_color=COLORS["bg_card"],
                          text_color=COLORS["text_primary"],
                          font=FONT["body"], width=540).pack(anchor="w")

        # ---- Description ----
        AppLabel(body, "Description / Details *", style="label_bold").pack(anchor="w", pady=(12, 4))
        ctk.CTkLabel(body, text="Describe what is wrong or why it's being returned:",
                     font=FONT["body_sm"], text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))
        self.desc_text = ctk.CTkTextbox(body, height=80, width=540,
                                         fg_color=COLORS["bg_input"],
                                         border_color=COLORS["border"],
                                         text_color=COLORS["text_primary"],
                                         scrollbar_button_color=COLORS["border"],
                                         font=FONT["body"],
                                         corner_radius=8, border_width=1)
        self.desc_text.pack(anchor="w")

        Divider(body).pack(fill="x", pady=12)

        # ---- Options row ----
        opts = ctk.CTkFrame(body, fg_color="transparent")
        opts.pack(fill="x")

        # Restock
        col_a = ctk.CTkFrame(opts, fg_color="transparent")
        col_a.pack(side="left", padx=(0, 32))
        AppLabel(col_a, "Add back to Stock?", style="label_bold").pack(anchor="w", pady=(0, 6))
        self.v_restock = tk.BooleanVar(value=True)
        ctk.CTkSwitch(col_a, text="Yes, restock this item",
                      variable=self.v_restock,
                      fg_color=COLORS["bg_input"],
                      progress_color=COLORS["success"],
                      text_color=COLORS["text_primary"],
                      font=FONT["body"]).pack(anchor="w")

        # Refund method
        col_b = ctk.CTkFrame(opts, fg_color="transparent")
        col_b.pack(side="left")
        AppLabel(col_b, "Refund Method", style="label_bold").pack(anchor="w", pady=(0, 6))
        self.v_refund_method = tk.StringVar(value="Cash")
        ctk.CTkOptionMenu(col_b, values=REFUND_METHODS, variable=self.v_refund_method,
                          fg_color=COLORS["bg_input"],
                          button_color=COLORS["accent"],
                          dropdown_fg_color=COLORS["bg_card"],
                          text_color=COLORS["text_primary"],
                          font=FONT["body"], width=200).pack(anchor="w")

        # ---- Customer (optional) ----
        Divider(body).pack(fill="x", pady=12)
        AppLabel(body, "Customer (optional)", style="label_bold").pack(anchor="w", pady=(0, 4))
        self._selected_customer = None
        cust_row = ctk.CTkFrame(body, fg_color="transparent")
        cust_row.pack(fill="x")
        self.cust_lbl = ctk.CTkLabel(cust_row, text="Walk-in / Not specified",
                                      font=FONT["body"],
                                      text_color=COLORS["text_secondary"])
        self.cust_lbl.pack(side="left")
        AppButton(cust_row, "Select", command=self._pick_customer,
                  style="ghost", width=80, height=30).pack(side="right")

        self._footer(on_cancel=self.destroy, on_confirm=self._save,
                     confirm_text="Process Return", confirm_style="danger")

    def _update_refund(self, *_):
        try:
            qty   = float(self.v_qty.get() or 0)
            price = float(self.v_price.get() or 0)
            total = qty * price
            currency = business.get_setting(self.session, "currency", "Rs.")
            self.refund_lbl.configure(text=f"Refund Total: {currency} {total:,.0f}")
        except Exception:
            pass

    def _on_prod_search(self, *_):
        if self._suppress_search:
            return
        query = self.v_prod.get().strip()
        for w in self.dropdown.winfo_children():
            w.destroy()
        self._selected_product = None
        self.prod_info.configure(text="")

        if len(query) < 1:
            self.dropdown.configure(height=0)
            return

        products = business.search_products(self.session, query)[:10]
        if not products:
            self.dropdown.configure(height=36)
            ctk.CTkLabel(self.dropdown, text="No products found.",
                         font=FONT["body_sm"],
                         text_color=COLORS["text_muted"]).pack(pady=6)
            return

        self.dropdown.configure(height=min(len(products) * 42, 180))
        currency = business.get_setting(self.session, "currency", "Rs.")

        for p in products:
            size_str = f" [{p.display_size}]" if p.display_size else ""
            row = ctk.CTkFrame(self.dropdown, fg_color="transparent", cursor="hand2")
            row.pack(fill="x", pady=1)
            lbl = ctk.CTkLabel(row,
                text=f"{p.name}{size_str}  ·  {p.category}  ·  Stock: {p.current_stock:.0f}",
                font=FONT["body"], text_color=COLORS["text_primary"], anchor="w")
            lbl.pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=f"{currency} {p.selling_price:,.0f}",
                         font=FONT["body_sm"], text_color=COLORS["accent"]).pack(side="right", padx=8)

            def pick(prod=p):
                self._selected_product = prod
                self._suppress_search = True
                self.v_prod.set(prod.name + (f" [{prod.display_size}]" if prod.display_size else ""))
                self._suppress_search = False
                self.v_price.set(str(prod.selling_price))
                for w in self.dropdown.winfo_children():
                    w.destroy()
                self.dropdown.configure(height=0)
                self.prod_info.configure(
                    text=f"✅ Selected: {prod.name}  |  Current stock: {prod.current_stock:.0f} {prod.unit}")

            for w in [row, lbl]:
                w.bind("<Button-1>", lambda e, fn=pick: fn())
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=COLORS["bg_hover"]))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color="transparent"))

    def _lookup_invoice(self):
        inv_no = self.v_invoice.get().strip()
        if not inv_no:
            return
        from models import Sale
        sale = self.session.query(Sale).filter_by(invoice_number=inv_no).first()
        if not sale:
            self.invoice_info.configure(
                text=f"❌ Invoice '{inv_no}' not found.",
                text_color=COLORS["danger"])
            return
        self._linked_sale = sale
        items_str = ", ".join(f"{si.product_name} x{si.quantity:.0f}" for si in sale.sale_items)
        self.invoice_info.configure(
            text=f"✅ Found: {sale.customer_name}  |  {sale.date.strftime('%d %b %Y')}  |  Items: {items_str}",
            text_color=COLORS["success"])

    def _pick_customer(self):
        from screen_billing import CustomerPickerDialog
        CustomerPickerDialog(self, self.session, on_select=self._set_customer)

    def _set_customer(self, c):
        self._selected_customer = c
        self.cust_lbl.configure(
            text=f"{c.name}  |  📞 {c.phone or '—'}",
            text_color=COLORS["text_primary"])

    def _save(self):
        if not self._selected_product:
            show_error(self, "Please select a product.")
            return
        try:
            qty   = float(self.v_qty.get())
            price = float(self.v_price.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            show_error(self, "Quantity and price must be valid numbers.")
            return

        desc = self.desc_text.get("1.0", "end").strip()
        if not desc:
            show_error(self, "Please enter a description for the return.")
            return

        sale_id = self._linked_sale.id if self._linked_sale else None

        try:
            ret = business.process_return(
                self.session,
                product_id=self._selected_product.id,
                quantity=qty,
                reason=self.v_reason.get(),
                description=desc,
                unit_price=price,
                restock=self.v_restock.get(),
                refund_method=self.v_refund_method.get(),
                customer_id=self._selected_customer.id if self._selected_customer else None,
                sale_id=sale_id,
            )
        except Exception as e:
            show_error(self, str(e))
            return

        currency = business.get_setting(self.session, "currency", "Rs.")
        msg = (f"Return {ret.return_number} processed.\n"
               f"Refund: {currency} {ret.refund_total:,.0f}  |  Method: {ret.refund_method}\n"
               f"{'Stock restored ✅' if ret.restock else 'Stock NOT restocked'}")
        show_info(self, msg, "Return Processed")
        if self.on_save:
            self.on_save()
        self.destroy()


# ---------------------------------------------------------------------------
# Return Detail Dialog
# ---------------------------------------------------------------------------

class ReturnDetailDialog(ModalDialog):
    def __init__(self, parent, ret, currency):
        super().__init__(parent, f"Return Detail — {ret.return_number}",
                         width=500, height=420)
        self._build(ret, currency)

    def _build(self, r, currency):
        self._header(f"Return — {r.return_number}")
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        def row(label, value, color=None):
            f = ctk.CTkFrame(body, fg_color="transparent")
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"], width=160, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=str(value), font=FONT["body"],
                         text_color=color or COLORS["text_primary"]).pack(side="left", padx=(8, 0))

        row("Return #",    r.return_number, COLORS["text_accent"])
        row("Date",        r.created_at.strftime("%d %B %Y  %H:%M"))
        row("Product",     r.product_name)
        row("Customer",    r.customer_name)
        row("Quantity",    f"{r.quantity:.0f}")
        row("Unit Price",  f"{currency} {r.unit_price:,.0f}")
        row("Refund Total", f"{currency} {r.refund_total:,.0f}", COLORS["danger"])
        row("Refund Method", r.refund_method)
        row("Restocked",   "Yes ✅" if r.restock else "No ❌",
            COLORS["success"] if r.restock else COLORS["text_muted"])
        row("Reason",      r.reason, COLORS["warning"])

        if r.description:
            Divider(body).pack(fill="x", pady=8)
            AppLabel(body, "Description:", style="label_bold").pack(anchor="w")
            ctk.CTkLabel(body, text=r.description, font=FONT["body"],
                         text_color=COLORS["text_secondary"],
                         wraplength=440, justify="left").pack(anchor="w", pady=(4, 0))

        AppButton(self, "Close", command=self.destroy, style="ghost",
                  width=100, height=36).pack(pady=(0, 12))
