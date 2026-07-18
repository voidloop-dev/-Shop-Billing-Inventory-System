"""
Stock Check Screen — instant product availability lookup.
Counter staff uses this when a customer asks "do you have X?"
Shows: name, size, selling price, current stock, category.
"""

import customtkinter as ctk
import tkinter as tk
from theme import (
    COLORS, FONT, Card, AppButton, AppEntry, AppLabel, Divider
)
import business


class StockCheckScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        AppLabel(top, "Stock Check", style="heading_lg").pack(side="left")
        ctk.CTkLabel(top, text="Check if a product is available — type any part of the name",
                     font=FONT["body"], text_color=COLORS["text_muted"]).pack(
            side="left", padx=(16, 0), pady=(4, 0))

        # Big search bar — center of attention
        search_card = Card(self)
        search_card.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 16))
        search_card.columnconfigure(0, weight=1)
        search_card.rowconfigure(1, weight=1)

        # Search input area
        search_area = ctk.CTkFrame(search_card, fg_color="transparent")
        search_area.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        search_inner = ctk.CTkFrame(search_area, fg_color="transparent")
        search_inner.pack(fill="x")

        # Big prominent search entry
        self.search_entry = ctk.CTkEntry(
            search_inner,
            placeholder_text="🔍  Type product name, size, or category…",
            textvariable=self.search_var,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border_focus"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            font=("Segoe UI", 16),
            corner_radius=10,
            border_width=2,
            height=52,
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.focus()
        self.search_entry.bind("<Escape>", lambda e: self._clear())

        AppButton(search_inner, "Clear", command=self._clear,
                  style="ghost", width=80, height=52).pack(side="left", padx=(8, 0))

        # Filter row
        filter_row = ctk.CTkFrame(search_area, fg_color="transparent")
        filter_row.pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(filter_row, text="Filter:",
                     font=FONT["label_bold"],
                     text_color=COLORS["text_secondary"]).pack(side="left")

        self.filter_var = tk.StringVar(value="All")
        self.filter_var.trace_add("write", lambda *_: self._on_search())

        for opt in ["All", "In Stock", "Low Stock", "Out of Stock"]:
            ctk.CTkRadioButton(
                filter_row, text=opt, value=opt, variable=self.filter_var,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color=COLORS["text_secondary"],
                font=FONT["body_sm"]
            ).pack(side="left", padx=(12, 0))

        # Results summary
        self.result_summary = ctk.CTkLabel(search_area, text="",
                                            font=FONT["body_sm"],
                                            text_color=COLORS["text_muted"])
        self.result_summary.pack(anchor="w", pady=(8, 0))

        # Divider
        Divider(search_card).grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 0))

        # Results table
        self.results_frame = ctk.CTkScrollableFrame(search_card, fg_color="transparent")
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        self._build_table_header()
        self._on_search()   # show all products initially

    def _build_table_header(self):
        hdr = ctk.CTkFrame(self.results_frame, fg_color="#F1F3F5", corner_radius=0)
        hdr.pack(fill="x")
        self._hdr = hdr
        cols = [
            ("Product Name", 240, "w"),
            ("Category", 130, "w"),
            ("Size", 90, "w"),
            ("Unit", 70, "w"),
            ("Sale Price", 110, "e"),
            ("In Stock", 100, "e"),
            ("Status", 110, "w"),
        ]
        for label, width, anchor in cols:
            ctk.CTkLabel(hdr, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"],
                         width=width, anchor=anchor).pack(side="left", padx=10, pady=10)

    def _on_search(self, *_):
        query = self.search_var.get().strip()
        products = business.search_products(self.session, query)

        # Apply stock filter
        flt = self.filter_var.get()
        if flt == "In Stock":
            products = [p for p in products if p.current_stock > p.low_stock_threshold]
        elif flt == "Low Stock":
            products = [p for p in products if 0 < p.current_stock <= p.low_stock_threshold]
        elif flt == "Out of Stock":
            products = [p for p in products if p.current_stock <= 0]

        # Clear old rows (keep header)
        for w in self.results_frame.winfo_children():
            if w is not self._hdr:
                w.destroy()

        count = len(products)
        if query:
            self.result_summary.configure(
                text=f"{count} product{'s' if count != 1 else ''} found for \"{query}\""
            )
        else:
            self.result_summary.configure(
                text=f"Showing all {count} products"
            )

        if not products:
            ctk.CTkLabel(self.results_frame,
                         text="No products match your search.\nTry different spelling or fewer letters.",
                         font=FONT["body_lg"], text_color=COLORS["text_muted"]).pack(pady=60)
            return

        currency = business.get_setting(self.session, "currency", "Rs.")
        for p in products:
            self._add_result_row(p, currency)

    def _add_result_row(self, p, currency):
        # Determine status
        if p.current_stock <= 0:
            status_txt   = "Out of Stock"
            status_color = COLORS["danger"]
            stock_color  = COLORS["danger"]
            row_bg       = COLORS["danger_dim"]
        elif p.is_low_stock:
            status_txt   = "Low Stock ⚠"
            status_color = COLORS["warning"]
            stock_color  = COLORS["warning"]
            row_bg       = COLORS["warning_dim"]
        else:
            status_txt   = "Available ✓"
            status_color = COLORS["success"]
            stock_color  = COLORS["success"]
            row_bg       = COLORS["bg_card"]

        row = ctk.CTkFrame(self.results_frame, fg_color=row_bg, corner_radius=8)
        row.pack(fill="x", pady=2, padx=0)
        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=COLORS["bg_hover"]))
        row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=row_bg))

        col_data = [
            (p.name, 240, "w", COLORS["text_primary"]),
            (p.category or "—", 130, "w", COLORS["text_secondary"]),
            (p.display_size or "—", 90, "w", COLORS["text_secondary"]),
            (p.unit, 70, "w", COLORS["text_muted"]),
            (f"{currency} {p.selling_price:,.0f}", 110, "e", COLORS["text_primary"]),
            (f"{p.current_stock:.1f}", 100, "e", stock_color),
        ]
        for text, width, anchor, color in col_data:
            ctk.CTkLabel(row, text=text, font=FONT["body"],
                         text_color=color, width=width, anchor=anchor).pack(
                side="left", padx=10, pady=10)

        # Status badge-style label
        ctk.CTkLabel(row, text=status_txt, font=FONT["label_bold"],
                     text_color=status_color, width=110, anchor="w").pack(
            side="left", padx=10)

        # Quick action: go to billing
        AppButton(row, "Add to Bill →",
                  command=lambda: self.navigate("billing"),
                  style="ghost", width=100, height=28).pack(side="right", padx=8)

    def _clear(self):
        self.search_var.set("")
        self.search_entry.focus()
