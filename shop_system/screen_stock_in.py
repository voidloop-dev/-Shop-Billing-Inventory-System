"""
Stock In Screen — restock products from suppliers.
Simple, fast, confirms before committing.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from theme import (
    COLORS, FONT, Card, AppButton, AppEntry, AppLabel,
    Divider, show_error, show_info
)
import business


class StockInScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self._selected_product = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        AppLabel(top, "Stock In — Restock", style="heading_lg").pack(side="left")

        # Main area
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 16))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, minsize=340)

        self._build_form(main)
        self._build_recent(main)

    def _build_form(self, parent):
        card = Card(parent)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=24)

        AppLabel(inner, "Add Stock", style="heading_sm").pack(anchor="w", pady=(0, 20))

        # Product search
        AppLabel(inner, "Select Product *", style="label_bold").pack(anchor="w", pady=(0, 4))
        self.prod_var = tk.StringVar()
        self.prod_var.trace_add("write", self._on_prod_search)
        self.prod_entry = AppEntry(inner, placeholder="Search product…",
                                   textvariable=self.prod_var, width=460)
        self.prod_entry.pack(anchor="w")

        self.dropdown = ctk.CTkScrollableFrame(inner, fg_color=COLORS["bg_card"],
                                               corner_radius=8, height=0)
        self.dropdown.pack(fill="x", pady=(4, 0))

        # Selected product info
        self.prod_info = ctk.CTkLabel(inner, text="",
                                       font=FONT["body_sm"],
                                       text_color=COLORS["text_secondary"])
        self.prod_info.pack(anchor="w", pady=(4, 12))

        # Quantity
        AppLabel(inner, "Quantity Received *", style="label_bold").pack(anchor="w", pady=(0, 4))
        self.qty_var = tk.StringVar()
        AppEntry(inner, placeholder="How many units received",
                 textvariable=self.qty_var, width=460).pack(anchor="w")

        # Supplier / note
        AppLabel(inner, "Supplier / Note (optional)", style="label_bold").pack(anchor="w", pady=(12, 4))
        self.note_var = tk.StringVar()
        AppEntry(inner, placeholder="e.g. National Traders, paid cash",
                 textvariable=self.note_var, width=460).pack(anchor="w")

        # Date display
        today = datetime.now().strftime("%A, %d %B %Y")
        ctk.CTkLabel(inner, text=f"Date: {today}", font=FONT["body_sm"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(12, 0))

        AppButton(inner, "✅  Add to Stock", command=self._submit,
                  style="success", width=460, height=44).pack(pady=(20, 0))

        # Feedback label
        self.status_lbl = ctk.CTkLabel(inner, text="", font=FONT["body"],
                                        text_color=COLORS["success"])
        self.status_lbl.pack(anchor="w", pady=(8, 0))

    def _build_recent(self, parent):
        card = Card(parent)
        card.grid(row=0, column=1, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        AppLabel(inner, "Recent Stock-Ins", style="heading_sm").pack(anchor="w", pady=(0, 12))

        self.recent_frame = ctk.CTkScrollableFrame(inner, fg_color="transparent")
        self.recent_frame.pack(fill="both", expand=True)
        self._refresh_recent()

    def _refresh_recent(self):
        for w in self.recent_frame.winfo_children():
            w.destroy()

        from models import StockMovement
        movements = (
            self.session.query(StockMovement)
            .filter_by(movement_type="IN")
            .order_by(StockMovement.created_at.desc())
            .limit(20)
            .all()
        )

        if not movements:
            ctk.CTkLabel(self.recent_frame, text="No stock-ins recorded yet.",
                         font=FONT["body_sm"],
                         text_color=COLORS["text_muted"]).pack(pady=20)
            return

        currency = business.get_setting(self.session, "currency", "Rs.")
        for mv in movements:
            row = ctk.CTkFrame(self.recent_frame, fg_color=COLORS["bg_card"], corner_radius=8)
            row.pack(fill="x", pady=2)

            p = mv.product
            name = p.name if p else "Unknown"
            size = f" [{p.display_size}]" if p and p.display_size else ""
            date_str = mv.created_at.strftime("%d %b  %H:%M")

            ctk.CTkLabel(row, text=f"{name}{size}", font=FONT["body_sm"],
                         text_color=COLORS["text_primary"], anchor="w",
                         width=140).pack(side="left", padx=8, pady=8)
            ctk.CTkLabel(row, text=f"+{mv.quantity:.0f}", font=FONT["label_bold"],
                         text_color=COLORS["success"], width=50).pack(side="left")
            ctk.CTkLabel(row, text=date_str, font=FONT["body_sm"],
                         text_color=COLORS["text_muted"]).pack(side="right", padx=8)

    # ------------------------------------------------------------------

    def _on_prod_search(self, *_):
        query = self.prod_var.get().strip()
        for w in self.dropdown.winfo_children():
            w.destroy()
        self._selected_product = None
        self.prod_info.configure(text="")

        if not query:
            self.dropdown.configure(height=0)
            return

        products = business.search_products(self.session, query)[:10]
        if not products:
            self.dropdown.configure(height=40)
            ctk.CTkLabel(self.dropdown, text="No products found.",
                         font=FONT["body_sm"],
                         text_color=COLORS["text_muted"]).pack(pady=8)
            return

        self.dropdown.configure(height=min(len(products) * 42, 200))
        currency = business.get_setting(self.session, "currency", "Rs.")

        for p in products:
            size_str = f" [{p.display_size}]" if p.display_size else ""
            row = ctk.CTkFrame(self.dropdown, fg_color="transparent", cursor="hand2")
            row.pack(fill="x", pady=1)
            lbl = ctk.CTkLabel(row,
                text=f"{p.name}{size_str}  ·  {p.category}  ·  Stock: {p.current_stock:.0f}",
                font=FONT["body"], text_color=COLORS["text_primary"], anchor="w")
            lbl.pack(side="left", padx=8, pady=6)

            def pick(prod=p):
                self._selected_product = prod
                self.prod_var.set(prod.name + (f" [{prod.display_size}]" if prod.display_size else ""))
                for w in self.dropdown.winfo_children():
                    w.destroy()
                self.dropdown.configure(height=0)
                self.prod_info.configure(
                    text=f"Current stock: {prod.current_stock:.1f} {prod.unit}  |  "
                         f"Cost: {currency} {prod.cost_price:,.0f}  |  "
                         f"Sell: {currency} {prod.selling_price:,.0f}"
                )

            for w in [row, lbl]:
                w.bind("<Button-1>", lambda e, fn=pick: fn())
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=COLORS["bg_hover"]))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color="transparent"))

    def _submit(self):
        if not self._selected_product:
            show_error(self, "Please select a product first.")
            return
        try:
            qty = float(self.qty_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            show_error(self, "Quantity must be a positive number.")
            return

        note = self.note_var.get().strip()
        business.stock_in(self.session, self._selected_product.id, qty, note)

        p = self._selected_product
        new_stock = p.current_stock  # already updated by business.stock_in
        self.status_lbl.configure(
            text=f"✅  Added {qty:.0f} units to {p.name}.  New stock: {new_stock:.0f} {p.unit}"
        )

        # Reset form
        self.prod_var.set("")
        self.qty_var.set("")
        self.note_var.set("")
        self._selected_product = None

        self._refresh_recent()
        # Clear status after 5 seconds
        self.after(5000, lambda: self.status_lbl.configure(text=""))
