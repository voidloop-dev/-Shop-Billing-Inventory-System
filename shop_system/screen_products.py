"""
Products Screen — manage the catalog.
List / search / add / edit / deactivate products.
"""

import customtkinter as ctk
import tkinter as tk
from theme import (
    COLORS, FONT, Card, AppButton, AppEntry, AppLabel,
    SearchBar, IconButton, Divider, ModalDialog,
    show_error, show_info, confirm_dialog
)
import business


SIZE_UNITS = ["N/A", "inch", "mm", "feet", "meter"]
UNITS      = ["piece", "box", "set", "meter", "feet", "kg", "liter", "roll"]


class ProductsScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()
        self.refresh()

    # ------------------------------------------------------------------

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))

        AppLabel(top, "Products", style="heading_lg").pack(side="left")

        AppButton(top, "+ Add Product", command=self._open_add,
                  width=140, height=38).pack(side="right")

        self.search = SearchBar(top, placeholder="Search by name, category, size…",
                                on_change=self._on_search, width=300)
        self.search.pack(side="right", padx=(0, 12))

        # Table container
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 16))
        self.table_frame.columnconfigure(0, weight=1)

        # Table headers
        self._build_header()

    def _build_header(self):
        hdr = ctk.CTkFrame(self.table_frame, fg_color="#F1F3F5", corner_radius=8)
        hdr.pack(fill="x", pady=(0, 4))
        cols = [("Product", 220, "w"), ("Category", 120, "w"), ("Size", 90, "w"),
                ("Unit", 70, "w"), ("Cost", 90, "e"), ("Price", 90, "e"),
                ("Stock", 80, "e"), ("", 130, "w")]
        for label, width, anchor in cols:
            ctk.CTkLabel(hdr, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"],
                         width=width, anchor=anchor).pack(side="left", padx=8, pady=8)

    def refresh(self, query=""):
        # Clear existing rows
        for w in self.table_frame.winfo_children()[1:]:  # keep header
            w.destroy()

        products = business.search_products(self.session, query)
        currency = business.get_setting(self.session, "currency", "Rs.")

        if not products:
            ctk.CTkLabel(self.table_frame, text="No products found.",
                         font=FONT["body"], text_color=COLORS["text_muted"]).pack(pady=40)
            return

        for p in products:
            self._add_row(p, currency)

    def _add_row(self, p, currency):
        bg = COLORS["bg_card"]
        row = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=8)
        row.pack(fill="x", pady=2)

        # Hover effect
        def on_enter(e): row.configure(fg_color=COLORS["bg_hover"])
        def on_leave(e): row.configure(fg_color=bg)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        # Stock warning color
        stock_color = COLORS["warning"] if p.is_low_stock else COLORS["text_primary"]

        col_data = [
            (p.name, 220, "w", COLORS["text_primary"]),
            (p.category or "—", 120, "w", COLORS["text_secondary"]),
            (p.display_size or "—", 90, "w", COLORS["text_secondary"]),
            (p.unit, 70, "w", COLORS["text_secondary"]),
            (f"{currency} {p.cost_price:,.0f}", 90, "e", COLORS["text_muted"]),
            (f"{currency} {p.selling_price:,.0f}", 90, "e", COLORS["text_primary"]),
            (f"{p.current_stock:.1f}", 80, "e", stock_color),
        ]
        for text, width, anchor, color in col_data:
            ctk.CTkLabel(row, text=text, font=FONT["body"],
                         text_color=color, width=width, anchor=anchor).pack(
                side="left", padx=8, pady=8)

        # Actions cell
        actions = ctk.CTkFrame(row, fg_color="transparent", width=130)
        actions.pack(side="left", padx=8, pady=4)
        IconButton(actions, "Edit", command=lambda pid=p.id: self._open_edit(pid),
                   style="ghost").pack(side="left", padx=(0, 4))
        IconButton(actions, "Remove", command=lambda pid=p.id: self._deactivate(pid),
                   style="danger").pack(side="left")

    def _on_search(self, query):
        self.refresh(query)

    def _deactivate(self, product_id):
        p = self.session.query(business.Product).filter_by(id=product_id).first()
        if not confirm_dialog(self, "Remove Product",
                              f"Hide '{p.name}' from the catalog?\n"
                              "Past invoices will still show it correctly."):
            return
        business.deactivate_product(self.session, product_id)
        self.refresh(self.search.get())

    def _open_add(self):
        ProductDialog(self, self.session, on_save=lambda: self.refresh(self.search.get()))

    def _open_edit(self, product_id):
        p = self.session.query(business.Product).filter_by(id=product_id).first()
        ProductDialog(self, self.session, product=p,
                      on_save=lambda: self.refresh(self.search.get()))


# ---------------------------------------------------------------------------
# Add / Edit Product Dialog
# ---------------------------------------------------------------------------

class ProductDialog(ModalDialog):
    def __init__(self, parent, session, product=None, on_save=None):
        title = "Edit Product" if product else "Add Product"
        super().__init__(parent, title, width=560, height=580)
        self.session = session
        self.product = product
        self.on_save = on_save
        self._build()
        if product:
            self._populate()

    def _build(self):
        self._header("Product Details")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        def field(label, var, placeholder="", width=480):
            ctk.CTkLabel(body, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(10, 2))
            e = AppEntry(body, placeholder=placeholder, width=width, textvariable=var)
            e.pack(anchor="w")
            return e

        def dropdown(label, var, values):
            ctk.CTkLabel(body, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(10, 2))
            m = ctk.CTkOptionMenu(body, values=values, variable=var,
                                  fg_color=COLORS["bg_input"],
                                  button_color=COLORS["accent"],
                                  dropdown_fg_color=COLORS["bg_card"],
                                  text_color=COLORS["text_primary"],
                                  font=FONT["body"], width=480)
            m.pack(anchor="w")

        self.v_name     = tk.StringVar()
        self.v_category = tk.StringVar(value="General")
        self.v_unit     = tk.StringVar(value="piece")
        self.v_size_val = tk.StringVar()
        self.v_size_unit = tk.StringVar(value="N/A")
        self.v_cost     = tk.StringVar()
        self.v_price    = tk.StringVar()
        self.v_stock    = tk.StringVar(value="0")
        self.v_threshold = tk.StringVar(value="5")

        field("Product Name *", self.v_name, "e.g. PVC Pipe, Ball Valve…")
        field("Category", self.v_category, "e.g. Pipes, Fittings, Valves…")
        dropdown("Unit", self.v_unit, UNITS)

        # Size row
        size_row = ctk.CTkFrame(body, fg_color="transparent")
        size_row.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(size_row, text="Size", font=FONT["label_bold"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w")
        sz_inner = ctk.CTkFrame(size_row, fg_color="transparent")
        sz_inner.pack(fill="x", pady=(4, 0))
        AppEntry(sz_inner, placeholder='e.g. 1/2, 3/4, 1…',
                 width=220, textvariable=self.v_size_val).pack(side="left")
        ctk.CTkOptionMenu(sz_inner, values=SIZE_UNITS, variable=self.v_size_unit,
                          fg_color=COLORS["bg_input"],
                          button_color=COLORS["accent"],
                          dropdown_fg_color=COLORS["bg_card"],
                          text_color=COLORS["text_primary"],
                          font=FONT["body"], width=250).pack(side="left", padx=(8, 0))

        # Prices row
        price_row = ctk.CTkFrame(body, fg_color="transparent")
        price_row.pack(fill="x", pady=(10, 0))
        for label, var, ph in [
            ("Cost Price (Rs.)", self.v_cost, "0"),
            ("Selling Price (Rs.)", self.v_price, "0"),
        ]:
            col = ctk.CTkFrame(price_row, fg_color="transparent")
            col.pack(side="left", padx=(0, 16))
            ctk.CTkLabel(col, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"], anchor="w").pack(anchor="w", pady=(0, 2))
            AppEntry(col, placeholder=ph, width=220, textvariable=var).pack()

        # Stock row (only editable on add)
        stock_row = ctk.CTkFrame(body, fg_color="transparent")
        stock_row.pack(fill="x", pady=(10, 0))
        for label, var, ph, editable in [
            ("Opening Stock", self.v_stock, "0", self.product is None),
            ("Low-Stock Alert at", self.v_threshold, "5", True),
        ]:
            col = ctk.CTkFrame(stock_row, fg_color="transparent")
            col.pack(side="left", padx=(0, 16))
            ctk.CTkLabel(col, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"], anchor="w").pack(anchor="w", pady=(0, 2))
            e = AppEntry(col, placeholder=ph, width=220, textvariable=var)
            e.pack()
            if not editable:
                e.configure(state="disabled",
                            text_color=COLORS["text_muted"],
                            placeholder_text_color=COLORS["text_muted"])

        if self.product:
            ctk.CTkLabel(body, text="To change stock, use Stock In from the sidebar.",
                         font=FONT["body_sm"],
                         text_color=COLORS["text_muted"]).pack(anchor="w", pady=(4, 0))

        self._footer(on_cancel=self.destroy, on_confirm=self._save, confirm_text="Save Product")

    def _populate(self):
        p = self.product
        self.v_name.set(p.name)
        self.v_category.set(p.category or "")
        self.v_unit.set(p.unit)
        self.v_size_val.set(p.size_value or "")
        self.v_size_unit.set(p.size_unit or "N/A")
        self.v_cost.set(str(p.cost_price))
        self.v_price.set(str(p.selling_price))
        self.v_stock.set(str(p.current_stock))
        self.v_threshold.set(str(p.low_stock_threshold))

    def _save(self):
        name = self.v_name.get().strip()
        if not name:
            show_error(self, "Product name is required.")
            return
        try:
            cost  = float(self.v_cost.get() or 0)
            price = float(self.v_price.get() or 0)
            stock = float(self.v_stock.get() or 0)
            threshold = float(self.v_threshold.get() or 5)
        except ValueError:
            show_error(self, "Prices and quantities must be numbers.")
            return

        kwargs = dict(
            name=name,
            category=self.v_category.get().strip() or "General",
            unit=self.v_unit.get(),
            size_value=self.v_size_val.get().strip(),
            size_unit=self.v_size_unit.get(),
            cost_price=cost,
            selling_price=price,
            low_stock_threshold=threshold,
        )

        if self.product:
            business.update_product(self.session, self.product.id, **kwargs)
        else:
            kwargs["initial_stock"] = stock
            business.add_product(self.session, **kwargs)

        if self.on_save:
            self.on_save()
        self.destroy()
