"""
Dashboard Screen — the home screen after login.
Shows today's sales, low-stock alerts, and quick-action buttons.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import date
from theme import (
    COLORS, FONT, Card, StatCard, AppButton, AppLabel,
    Divider, StatusBadge
)
import business


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Page header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 0))

        shop = business.get_setting(self.session, "shop_name", "My Shop")
        today = date.today().strftime("%A, %d %B %Y")
        AppLabel(hdr, text=f"Good day — {shop}", style="heading_lg").pack(side="left")
        AppLabel(hdr, text=today, style="muted").pack(side="right", pady=(6, 0))

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=32, pady=16)
        scroll.columnconfigure(0, weight=1)

        self._build_stats(scroll)
        self._build_quick_actions(scroll)
        self._build_low_stock(scroll)
        self._build_recent_sales(scroll)

    def _build_stats(self, parent):
        report = business.daily_sales_report(self.session)
        currency = business.get_setting(self.session, "currency", "Rs.")

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 20))
        for i in range(4):
            frame.columnconfigure(i, weight=1)

        cards = [
            ("Today's Sales", f"{len(report['sales'])}", "invoices", COLORS["accent"]),
            ("Revenue", f"{currency} {report['total_revenue']:,.0f}", "collected today", COLORS["success"]),
            ("Collected", f"{currency} {report['total_collected']:,.0f}", "cash received", COLORS["success"]),
            ("Outstanding Due", f"{currency} {report['total_due']:,.0f}", "from today", COLORS["warning"]),
        ]
        for i, (label, value, sub, color) in enumerate(cards):
            StatCard(frame, label=label, value=value, sub=sub, accent_color=color).grid(
                row=0, column=i, padx=(0 if i == 0 else 10), sticky="ew"
            )

    def _build_quick_actions(self, parent):
        AppLabel(parent, text="Quick Actions", style="heading_sm").pack(anchor="w", pady=(0, 10))

        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 24))

        buttons = [
            ("🧾  New Sale",    "billing",   COLORS["accent"],      COLORS["accent_hover"]),
            ("📦  Stock In",    "stock_in",  "#1D6FA8",             "#155A8A"),
            ("👥  Customers",   "customers", "#6B4C96",             "#56399E"),
            ("📊  Reports",     "reports",   "#B45309",             "#92400E"),
        ]
        for text, target, fg, hover in buttons:
            ctk.CTkButton(
                actions, text=text,
                command=lambda t=target: self.navigate(t),
                fg_color=fg, hover_color=hover,
                text_color=COLORS["text_primary"],
                font=FONT["heading_sm"],
                height=54, corner_radius=10,
                width=160
            ).pack(side="left", padx=(0, 12))

    def _build_low_stock(self, parent):
        low = business.get_low_stock_products(self.session)
        if not low:
            return

        card = Card(parent)
        card.pack(fill="x", pady=(0, 20))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(hdr, text="⚠️  Low Stock Alert",
                     font=FONT["heading_sm"],
                     text_color=COLORS["warning"]).pack(side="left")
        ctk.CTkLabel(hdr, text=f"{len(low)} products",
                     font=FONT["body_sm"],
                     text_color=COLORS["text_muted"]).pack(side="right")

        Divider(card).pack(fill="x", padx=16)

        for p in low[:8]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row, text=p.name,
                         font=FONT["body"],
                         text_color=COLORS["text_primary"],
                         anchor="w").pack(side="left")
            size_txt = f"  ({p.display_size})" if p.display_size else ""
            ctk.CTkLabel(row, text=f"{p.category}{size_txt}",
                         font=FONT["body_sm"],
                         text_color=COLORS["text_muted"]).pack(side="left", padx=(4, 0))
            ctk.CTkLabel(row,
                         text=f"{p.current_stock:.0f} {p.unit} left",
                         font=FONT["label_bold"],
                         text_color=COLORS["warning"]).pack(side="right")

        AppButton(card, "Restock Now →", command=lambda: self.navigate("stock_in"),
                  style="ghost", width=130, height=32).pack(anchor="e", padx=16, pady=(8, 12))

    def _build_recent_sales(self, parent):
        report = business.daily_sales_report(self.session)
        sales = sorted(report["sales"], key=lambda s: s.date, reverse=True)[:10]
        currency = business.get_setting(self.session, "currency", "Rs.")

        AppLabel(parent, text="Today's Invoices", style="heading_sm").pack(
            anchor="w", pady=(0, 10)
        )

        if not sales:
            card = Card(parent)
            card.pack(fill="x")
            ctk.CTkLabel(card, text="No sales today. Start with New Sale ↑",
                         font=FONT["body"],
                         text_color=COLORS["text_muted"]).pack(pady=24)
            return

        card = Card(parent)
        card.pack(fill="x")

        # Header row
        hdr = ctk.CTkFrame(card, fg_color="#F1F3F5", corner_radius=0)
        hdr.pack(fill="x")
        for text, width in [("Invoice", 120), ("Customer", 200), ("Total", 120),
                             ("Paid", 120), ("Status", 90)]:
            ctk.CTkLabel(hdr, text=text, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"],
                         width=width, anchor="w").pack(side="left", padx=12, pady=8)

        for s in sales:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x")
            Divider(card).pack(fill="x", padx=0)

            for text, width in [
                (s.invoice_number, 120),
                (s.customer_name, 200),
                (f"{currency} {s.total:,.0f}", 120),
                (f"{currency} {s.amount_paid:,.0f}", 120),
            ]:
                ctk.CTkLabel(row, text=text, font=FONT["body"],
                             text_color=COLORS["text_primary"],
                             width=width, anchor="w").pack(side="left", padx=12, pady=8)

            StatusBadge(row, s.status).pack(side="left", padx=4)

        AppButton(card, "View All →", command=lambda: self.navigate("reports"),
                  style="ghost", width=110, height=30).pack(anchor="e", padx=12, pady=8)
