"""
Billing / New Sale Screen — the most important screen in the app.
Must be fast, clear, and forgiving. Used tens of times per day.
"""

import customtkinter as ctk
import tkinter as tk
from theme import (
    COLORS, FONT, Card, AppButton, AppEntry, AppLabel,
    Divider, IconButton, show_error, show_info, confirm_dialog
)
import business
from invoice_pdf import generate_invoice_pdf
import os, subprocess, sys


class BillingScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self.cart = []          # list of {product, quantity, unit_price}
        self.selected_customer = None
        self._suppress_search = False   # prevents search trace from firing when WE set the text
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        AppLabel(top, "New Sale", style="heading_lg").pack(side="left")
        AppButton(top, "Clear All", command=self._clear_all,
                  style="ghost", width=100, height=36).pack(side="right")

        # Main area: left = product search + cart | right = summary panel
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 16))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, minsize=320)
        main.rowconfigure(0, weight=1)

        self._build_left(main)
        self._build_right(main)

    def _build_left(self, parent):
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        # Customer selector
        cust_card = Card(left)
        cust_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._build_customer_selector(cust_card)

        # Product search
        prod_card = Card(left)
        prod_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self._build_product_search(prod_card)

        # Cart
        cart_card = Card(left)
        cart_card.grid(row=2, column=0, sticky="nsew")
        self._build_cart(cart_card)

    def _build_customer_selector(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        AppLabel(inner, "Customer", style="label_bold").pack(side="left")

        self.cust_display = ctk.CTkLabel(inner, text="Walk-in (no customer)",
                                          font=FONT["body"],
                                          text_color=COLORS["text_secondary"])
        self.cust_display.pack(side="left", padx=(12, 0))

        AppButton(inner, "Select", command=self._open_customer_picker,
                  style="ghost", width=80, height=30).pack(side="right")
        AppButton(inner, "Clear", command=self._clear_customer,
                  style="ghost", width=70, height=30).pack(side="right", padx=(0, 4))

    def _build_product_search(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        AppLabel(inner, "Add Product to Bill", style="label_bold").pack(anchor="w", pady=(0, 8))

        search_row = ctk.CTkFrame(inner, fg_color="transparent")
        search_row.pack(fill="x")

        self.prod_search_var = tk.StringVar()
        self.prod_search_var.trace_add("write", self._on_prod_search)
        self.prod_entry = AppEntry(search_row, placeholder="Search product name or size…",
                                   textvariable=self.prod_search_var, width=340)
        self.prod_entry.pack(side="left")
        self.prod_entry.bind("<Down>", self._focus_dropdown)
        self.prod_entry.bind("<Return>", self._focus_dropdown)

        self.qty_var = tk.StringVar(value="1")
        AppEntry(search_row, placeholder="Qty", textvariable=self.qty_var,
                 width=70).pack(side="left", padx=(8, 0))

        AppButton(search_row, "Add", command=self._add_selected_to_cart,
                  width=80, height=38).pack(side="left", padx=(8, 0))

        # Dropdown results
        self.dropdown_frame = ctk.CTkScrollableFrame(
            inner, fg_color=COLORS["bg_card"],
            corner_radius=8, height=0, border_width=1, border_color=COLORS["border"]
        )
        self.dropdown_frame.pack(fill="x", pady=(4, 0))
        self._dropdown_products = []
        self._selected_product = None

    def _build_cart(self, parent):
        # Header
        hdr = ctk.CTkFrame(parent, fg_color="#F1F3F5", corner_radius=0)
        hdr.pack(fill="x")
        for text, width in [("Product", 220), ("Qty", 60), ("Price", 100), ("Total", 100), ("", 50)]:
            ctk.CTkLabel(hdr, text=text, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"],
                         width=width, anchor="w").pack(side="left", padx=8, pady=8)

        self.cart_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.cart_frame.pack(fill="both", expand=True)

        self.empty_label = ctk.CTkLabel(
            self.cart_frame,
            text="No items yet.\nSearch and add products above ↑",
            font=FONT["body"], text_color=COLORS["text_muted"]
        )
        self.empty_label.pack(pady=40)

    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent", width=330)
        right.grid(row=0, column=1, sticky="ns")
        right.pack_propagate(False)

        # Summary card
        summary = Card(right)
        summary.pack(fill="x", pady=(0, 12))

        inner = ctk.CTkFrame(summary, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        AppLabel(inner, "Bill Summary", style="heading_sm").pack(anchor="w", pady=(0, 12))

        # Subtotal
        self._subtotal_lbl = self._summary_row(inner, "Subtotal", "Rs. 0")

        # ---- DISCOUNT SECTION ----
        disc_hdr = ctk.CTkFrame(inner, fg_color="transparent")
        disc_hdr.pack(fill="x", pady=(10, 0))
        AppLabel(disc_hdr, "Discount", style="label_bold").pack(side="left")

        # Customer default badge
        self._cust_disc_badge = ctk.CTkLabel(
            disc_hdr, text="",
            font=FONT["body_sm"],
            text_color=COLORS["text_accent"],
            fg_color=COLORS["accent_light"],
            corner_radius=6, padx=6, pady=1
        )
        # only pack when customer has a discount

        # Toggle: % or flat
        self.disc_type_var = tk.StringVar(value="% Percent")
        ctk.CTkSegmentedButton(
            inner,
            values=["% Percent", "Flat (Rs.)"],
            command=self._on_disc_type_change,
            fg_color=COLORS["bg_input"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            font=FONT["body_sm"],
            variable=self.disc_type_var,
            width=290
        ).pack(fill="x", pady=(6, 0))

        # Discount value entry
        self.disc_var = tk.StringVar(value="0")
        self.disc_var.trace_add("write", lambda *_: self._refresh_totals())
        disc_entry_row = ctk.CTkFrame(inner, fg_color="transparent")
        disc_entry_row.pack(fill="x", pady=(6, 0))
        AppEntry(disc_entry_row, placeholder="Enter discount value",
                 textvariable=self.disc_var, width=200).pack(side="left")
        AppButton(disc_entry_row, "Reset",
                  command=lambda: self.disc_var.set("0"),
                  style="ghost", width=80, height=36).pack(side="left", padx=(6, 0))

        # Live computed discount hint
        self._disc_hint = ctk.CTkLabel(inner, text="",
                                        font=FONT["body_sm"],
                                        text_color=COLORS["text_muted"])
        self._disc_hint.pack(anchor="w", pady=(2, 0))

        Divider(inner).pack(fill="x", pady=10)
        self._disc_lbl  = self._summary_row(inner, "Discount (–)", "Rs. 0",
                                              val_color=COLORS["danger"])
        self._total_lbl = self._summary_row(inner, "TOTAL", "Rs. 0",
                                              key_font=FONT["heading_sm"],
                                              val_color=COLORS["accent"],
                                              val_font=FONT["heading_sm"])

        Divider(inner).pack(fill="x", pady=10)

        # Amount paid
        AppLabel(inner, "Amount Received (Rs.)", style="label_bold").pack(anchor="w", pady=(0, 4))
        self.paid_var = tk.StringVar(value="0")
        self.paid_var.trace_add("write", lambda *_: self._refresh_totals())
        AppEntry(inner, placeholder="Amount customer is paying now",
                 textvariable=self.paid_var, width=290).pack()

        # Full amount button
        AppButton(inner, "Set Full Amount",
                  command=self._set_full_amount,
                  style="ghost", width=140, height=28).pack(anchor="w", pady=(4, 0))

        Divider(inner).pack(fill="x", pady=10)
        self._due_lbl = self._summary_row(inner, "Amount Due", "Rs. 0",
                                           val_color=COLORS["warning"])

        # Notes
        AppLabel(inner, "Notes (optional)", style="label_bold").pack(anchor="w", pady=(10, 4))
        self.notes_var = tk.StringVar()
        AppEntry(inner, placeholder="Any note for this invoice…",
                 textvariable=self.notes_var, width=290).pack()

        # Action buttons
        btns = ctk.CTkFrame(right, fg_color="transparent")
        btns.pack(fill="x", pady=(8, 0))
        AppButton(btns, "💾  Save & Print Invoice",
                  command=self._complete_sale,
                  style="success", width=290, height=46).pack(fill="x", pady=(0, 8))
        AppButton(btns, "Save Only (No Print)",
                  command=lambda: self._complete_sale(print_invoice=False),
                  style="ghost", width=290, height=38).pack(fill="x")

    def _summary_row(self, parent, key, value, key_font=None, val_font=None,
                     val_color=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(row, text=key,
                     font=key_font or FONT["body"],
                     text_color=COLORS["text_secondary"]).pack(side="left")
        lbl = ctk.CTkLabel(row, text=value,
                            font=val_font or FONT["body"],
                            text_color=val_color or COLORS["text_primary"])
        lbl.pack(side="right")
        return lbl

    # ------------------------------------------------------------------
    # Customer picker
    # ------------------------------------------------------------------

    def _open_customer_picker(self):
        CustomerPickerDialog(self, self.session, on_select=self._set_customer)

    def _set_customer(self, customer):
        self.selected_customer = customer
        if customer:
            disc_txt = f"  [{customer.default_discount:.0f}% default disc]" if customer.default_discount else ""
            due_txt  = f"  |  Due: Rs. {customer.due_balance:,.0f}" if customer.due_balance > 0 else ""
            self.cust_display.configure(
                text=f"{customer.name}{disc_txt}  |  📞 {customer.phone or '—'}{due_txt}",
                text_color=COLORS["text_primary"]
            )
            # Auto-apply customer default discount
            if customer.default_discount and customer.default_discount > 0:
                self.disc_type_var.set("% Percent")
                self.disc_var.set(str(int(customer.default_discount)))
                self._cust_disc_badge.configure(
                    text=f"  Customer default: {customer.default_discount:.0f}%  "
                )
                self._cust_disc_badge.pack(side="right")
            else:
                self._cust_disc_badge.pack_forget()
        self._refresh_totals()

    def _clear_customer(self):
        self.selected_customer = None
        self.cust_display.configure(text="Walk-in (no customer)",
                                     text_color=COLORS["text_secondary"])
        self._cust_disc_badge.pack_forget()
        self.disc_var.set("0")
        self._refresh_totals()

    # ------------------------------------------------------------------
    # Product search & dropdown
    # ------------------------------------------------------------------

    def _on_prod_search(self, *_):
        # If WE set the text (after a selection), don't run the search — it would clear _selected_product
        if self._suppress_search:
            return

        query = self.prod_search_var.get().strip()
        # Clear dropdown and selection whenever user actually types
        for w in self.dropdown_frame.winfo_children():
            w.destroy()
        self._dropdown_products = []
        self._selected_product = None

        # Trigger search from just 1 character
        if len(query) < 1:
            self.dropdown_frame.configure(height=0)
            return

        products = business.search_products(self.session, query)[:12]
        self._dropdown_products = products

        if not products:
            self.dropdown_frame.configure(height=40)
            ctk.CTkLabel(self.dropdown_frame, text="No products found.",
                         font=FONT["body_sm"],
                         text_color=COLORS["text_muted"]).pack(pady=8)
            return

        self.dropdown_frame.configure(height=min(len(products) * 44, 220))
        currency = business.get_setting(self.session, "currency", "Rs.")

        for p in products:
            size_str = f"  [{p.display_size}]" if p.display_size else ""
            stock_color = COLORS["warning"] if p.is_low_stock else COLORS["text_muted"]
            stock_str = f"{p.current_stock:.0f} {p.unit}"

            row = ctk.CTkFrame(self.dropdown_frame, fg_color="transparent", cursor="hand2")
            row.pack(fill="x", pady=1)

            name_lbl = ctk.CTkLabel(row,
                text=f"{p.name}{size_str}  ·  {p.category}",
                font=FONT["body"], text_color=COLORS["text_primary"], anchor="w")
            name_lbl.pack(side="left", padx=8, pady=6)

            ctk.CTkLabel(row,
                text=f"{currency} {p.selling_price:,.0f}",
                font=FONT["body_sm"], text_color=COLORS["accent"]).pack(side="right", padx=4)
            ctk.CTkLabel(row,
                text=stock_str,
                font=FONT["body_sm"], text_color=stock_color).pack(side="right", padx=4)

            def on_click(event, prod=p):
                self._select_product(prod)
            for w in [row, name_lbl]:
                w.bind("<Button-1>", on_click)

            def on_enter(e, r=row): r.configure(fg_color=COLORS["bg_hover"])
            def on_leave(e, r=row): r.configure(fg_color="transparent")
            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)

    def _focus_dropdown(self, event=None):
        if self._dropdown_products:
            self._select_product(self._dropdown_products[0])

    def _select_product(self, product):
        self._selected_product = product

        # Suppress the search trace while we programmatically set the entry text
        # — otherwise the trace fires, sees the new text, and wipes _selected_product
        self._suppress_search = True
        self.prod_search_var.set(
            product.name + (f" [{product.display_size}]" if product.display_size else "")
        )
        self._suppress_search = False

        # Hide dropdown
        for w in self.dropdown_frame.winfo_children():
            w.destroy()
        self.dropdown_frame.configure(height=0)
        self.qty_var.set("1")

    def _add_selected_to_cart(self):
        if not self._selected_product:
            show_error(self, "Please select a product from the search results first.")
            return
        try:
            qty = float(self.qty_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            show_error(self, "Quantity must be a positive number.")
            return

        p = self._selected_product

        # Warn if overselling
        if qty > p.current_stock:
            if not confirm_dialog(self, "Low Stock Warning",
                f"Only {p.current_stock:.0f} {p.unit} in stock.\n"
                f"You're selling {qty:.0f}. Proceed anyway?\n\n"
                "(Stock will floor at zero, not go negative.)"):
                return

        # Check if already in cart — update quantity instead
        for item in self.cart:
            if item["product"].id == p.id:
                item["quantity"] += qty
                self._render_cart()
                self._refresh_totals()
                self._clear_search()
                return

        self.cart.append({
            "product": p,
            "quantity": qty,
            "unit_price": p.selling_price,
        })
        self._render_cart()
        self._refresh_totals()
        self._clear_search()

    def _clear_search(self):
        self._suppress_search = True
        self.prod_search_var.set("")
        self._suppress_search = False
        self._selected_product = None
        self._dropdown_products = []
        for w in self.dropdown_frame.winfo_children():
            w.destroy()
        self.dropdown_frame.configure(height=0)
        self.qty_var.set("1")
        self.prod_entry.focus()

    # ------------------------------------------------------------------
    # Cart rendering
    # ------------------------------------------------------------------

    def _render_cart(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()

        if not self.cart:
            self.empty_label = ctk.CTkLabel(
                self.cart_frame,
                text="No items yet.\nSearch and add products above ↑",
                font=FONT["body"], text_color=COLORS["text_muted"]
            )
            self.empty_label.pack(pady=40)
            return

        currency = business.get_setting(self.session, "currency", "Rs.")
        for idx, item in enumerate(self.cart):
            self._render_cart_row(idx, item, currency)

    def _render_cart_row(self, idx, item, currency):
        p   = item["product"]
        qty = item["quantity"]
        price = item["unit_price"]
        total = qty * price

        bg = COLORS["bg_card"] if idx % 2 == 0 else "#F8F9FA"
        row = ctk.CTkFrame(self.cart_frame, fg_color=bg, corner_radius=6)
        row.pack(fill="x", pady=2)

        size_str = f" [{p.display_size}]" if p.display_size else ""
        ctk.CTkLabel(row, text=f"{p.name}{size_str}",
                     font=FONT["body"], text_color=COLORS["text_primary"],
                     width=220, anchor="w").pack(side="left", padx=8, pady=8)

        # Editable quantity
        qty_var = tk.StringVar(value=str(qty))
        qty_entry = ctk.CTkEntry(row, textvariable=qty_var, width=55,
                                  fg_color=COLORS["bg_input"],
                                  border_color=COLORS["border"],
                                  text_color=COLORS["text_primary"],
                                  font=FONT["body"],
                                  corner_radius=6, border_width=1)
        qty_entry.pack(side="left", padx=4)

        def update_qty(e, i=idx, v=qty_var):
            try:
                new_qty = float(v.get())
                if new_qty > 0:
                    self.cart[i]["quantity"] = new_qty
                    self._render_cart()
                    self._refresh_totals()
            except ValueError:
                pass
        qty_entry.bind("<FocusOut>", update_qty)
        qty_entry.bind("<Return>", update_qty)

        # Editable price
        price_var = tk.StringVar(value=str(price))
        price_entry = ctk.CTkEntry(row, textvariable=price_var, width=90,
                                    fg_color=COLORS["bg_input"],
                                    border_color=COLORS["border"],
                                    text_color=COLORS["text_primary"],
                                    font=FONT["body"],
                                    corner_radius=6, border_width=1)
        price_entry.pack(side="left", padx=4)

        def update_price(e, i=idx, v=price_var):
            try:
                new_price = float(v.get())
                if new_price >= 0:
                    self.cart[i]["unit_price"] = new_price
                    self._render_cart()
                    self._refresh_totals()
            except ValueError:
                pass
        price_entry.bind("<FocusOut>", update_price)
        price_entry.bind("<Return>", update_price)

        ctk.CTkLabel(row, text=f"{currency} {total:,.0f}",
                     font=FONT["body"], text_color=COLORS["text_primary"],
                     width=100, anchor="w").pack(side="left", padx=4)

        IconButton(row, "✕", style="danger",
                   command=lambda i=idx: self._remove_item(i)).pack(side="left", padx=4)

    def _remove_item(self, idx):
        self.cart.pop(idx)
        self._render_cart()
        self._refresh_totals()

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------

    def _get_discount_type(self):
        return "percent" if "%" in self.disc_type_var.get() else "flat"

    def _on_disc_type_change(self, val):
        self._refresh_totals()

    def _set_full_amount(self):
        """Set the paid amount to the full total."""
        subtotal = sum(i["quantity"] * i["unit_price"] for i in self.cart)
        try:
            disc_val = float(self.disc_var.get() or 0)
        except ValueError:
            disc_val = 0.0
        disc_amount = business.compute_discount(subtotal, self._get_discount_type(), disc_val)
        total = max(subtotal - disc_amount, 0)
        self.paid_var.set(str(int(total)))

    def _refresh_totals(self):
        subtotal = sum(i["quantity"] * i["unit_price"] for i in self.cart)
        try:
            disc_val = float(self.disc_var.get() or 0)
        except ValueError:
            disc_val = 0.0
        try:
            paid = float(self.paid_var.get() or 0)
        except ValueError:
            paid = 0.0

        disc_type   = self._get_discount_type()
        disc_amount = business.compute_discount(subtotal, disc_type, disc_val)
        total = max(subtotal - disc_amount, 0)
        due   = max(total - paid, 0)

        currency = business.get_setting(self.session, "currency", "Rs.")
        self._subtotal_lbl.configure(text=f"{currency} {subtotal:,.0f}")
        self._disc_lbl.configure(text=f"– {currency} {disc_amount:,.0f}")
        self._total_lbl.configure(text=f"{currency} {total:,.0f}")
        self._due_lbl.configure(text=f"{currency} {due:,.0f}")

        # Hint: show what the discount equals in the other unit
        if disc_val > 0 and subtotal > 0:
            if disc_type == "percent":
                equiv = f"= {currency} {disc_amount:,.0f} off"
            else:
                pct = (disc_val / subtotal * 100) if subtotal else 0
                equiv = f"= {pct:.1f}% off"
            self._disc_hint.configure(text=equiv)
        else:
            self._disc_hint.configure(text="")

    # ------------------------------------------------------------------
    # Complete sale
    # ------------------------------------------------------------------

    def _complete_sale(self, print_invoice=True):
        if not self.cart:
            show_error(self, "Add at least one product to the bill.")
            return

        try:
            disc_val = float(self.disc_var.get() or 0)
            paid = float(self.paid_var.get() or 0)
        except ValueError:
            show_error(self, "Discount and amount paid must be numbers.")
            return

        items = [{"product_id": i["product"].id,
                  "quantity": i["quantity"],
                  "unit_price": i["unit_price"]} for i in self.cart]

        try:
            sale = business.create_sale(
                self.session,
                customer_id=self.selected_customer.id if self.selected_customer else None,
                items=items,
                discount_type=self._get_discount_type(),
                discount_value=disc_val,
                amount_paid=paid,
                notes=self.notes_var.get().strip()
            )
        except Exception as e:
            show_error(self, f"Could not complete sale: {e}")
            return

        if print_invoice:
            try:
                pdf_path = generate_invoice_pdf(self.session, sale)
                _open_pdf(pdf_path)
            except Exception as e:
                show_info(self, f"Sale saved! (PDF error: {e})\nInvoice: {sale.invoice_number}")
        else:
            show_info(self, f"Sale saved!\nInvoice: {sale.invoice_number}")

        self._clear_all()

    def _clear_all(self):
        self.cart = []
        self.selected_customer = None
        self.cust_display.configure(text="Walk-in (no customer)",
                                     text_color=COLORS["text_secondary"])
        self.disc_var.set("0")
        self.paid_var.set("0")
        self.notes_var.set("")
        self._clear_search()
        self._render_cart()
        self._refresh_totals()


# ---------------------------------------------------------------------------
# Customer Picker Dialog
# ---------------------------------------------------------------------------

class CustomerPickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, session, on_select):
        super().__init__(parent)
        self.session = session
        self.on_select = on_select
        self.title("Select Customer")
        self.geometry("500x500")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=COLORS["bg_base"])
        self._build()

    def _build(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        AppLabel(inner, "Select Customer", style="heading_md").pack(anchor="w", pady=(0, 12))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._refresh)
        AppEntry(inner, placeholder="Search by name or phone…",
                 textvariable=self.search_var, width=460).pack(pady=(0, 8))

        self.list_frame = ctk.CTkScrollableFrame(inner, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self, *_):
        for w in self.list_frame.winfo_children():
            w.destroy()
        query = self.search_var.get().strip()
        customers = business.search_customers(self.session, query)

        currency = business.get_setting(self.session, "currency", "Rs.")
        for c in customers:
            row = ctk.CTkFrame(self.list_frame, fg_color=COLORS["bg_card"],
                               corner_radius=8, cursor="hand2")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=c.name, font=FONT["body"],
                         text_color=COLORS["text_primary"], anchor="w").pack(
                side="left", padx=12, pady=10)
            if c.phone:
                ctk.CTkLabel(row, text=c.phone, font=FONT["body_sm"],
                             text_color=COLORS["text_muted"]).pack(side="left", padx=4)
            if c.due_balance > 0:
                ctk.CTkLabel(row, text=f"Due: {currency} {c.due_balance:,.0f}",
                             font=FONT["body_sm"],
                             text_color=COLORS["warning"]).pack(side="right", padx=12)

            def select(cust=c):
                self.on_select(cust)
                self.destroy()
            row.bind("<Button-1>", lambda e, fn=select: fn())
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=COLORS["bg_hover"]))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=COLORS["bg_card"]))


def _open_pdf(path):
    """Open a PDF with the system default viewer."""
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])
