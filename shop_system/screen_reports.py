"""
Reports Screen — daily and monthly summaries.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import date, datetime
from theme import (
    COLORS, FONT, Card, AppButton, AppEntry, AppLabel,
    Divider, StatusBadge
)
import business


class ReportsScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._current_tab = "daily"
        self._build()
        self._show_daily()

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        AppLabel(top, "Reports", style="heading_lg").pack(side="left")

        # Tab strip
        tabs = ctk.CTkFrame(top, fg_color="#F1F3F5", corner_radius=8)
        tabs.pack(side="left", padx=(24, 0))
        self.tab_daily = ctk.CTkButton(
            tabs, text="Daily", width=90, height=34,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_primary"], font=FONT["body"],
            corner_radius=6, command=self._show_daily
        )
        self.tab_daily.pack(side="left", padx=4, pady=4)
        self.tab_monthly = ctk.CTkButton(
            tabs, text="Monthly", width=90, height=34,
            fg_color="transparent", hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_secondary"], font=FONT["body"],
            corner_radius=6, command=self._show_monthly
        )
        self.tab_monthly.pack(side="left", padx=(0, 4), pady=4)

        # Scroll area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 16))
        self.scroll.columnconfigure(0, weight=1)

    def _clear_scroll(self):
        for w in self.scroll.winfo_children():
            w.destroy()

    def _set_active_tab(self, active):
        for btn, name in [(self.tab_daily, "daily"), (self.tab_monthly, "monthly")]:
            if name == active:
                btn.configure(fg_color=COLORS["accent"], text_color=COLORS["text_primary"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])

    # ------------------------------------------------------------------
    # Daily Report
    # ------------------------------------------------------------------

    def _show_daily(self):
        self._set_active_tab("daily")
        self._clear_scroll()

        # Date picker row
        ctrl = ctk.CTkFrame(self.scroll, fg_color="transparent")
        ctrl.pack(fill="x", pady=(0, 16))
        AppLabel(ctrl, "Date:", style="label_bold").pack(side="left")
        self.date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        AppEntry(ctrl, placeholder="YYYY-MM-DD", textvariable=self.date_var,
                 width=140).pack(side="left", padx=(8, 0))
        AppButton(ctrl, "Load", command=self._load_daily,
                  style="primary", width=80, height=34).pack(side="left", padx=(8, 0))
        AppButton(ctrl, "Today", command=self._load_today,
                  style="ghost", width=70, height=34).pack(side="left", padx=(4, 0))

        self.report_body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.report_body.pack(fill="x")

        self._load_daily()

    def _load_today(self):
        self.date_var.set(date.today().strftime("%Y-%m-%d"))
        self._load_daily()

    def _load_daily(self):
        for w in self.report_body.winfo_children():
            w.destroy()

        try:
            target = datetime.strptime(self.date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            AppLabel(self.report_body, "Invalid date. Use YYYY-MM-DD format.", style="body").pack()
            return

        report = business.daily_sales_report(self.session, target)
        currency = business.get_setting(self.session, "currency", "Rs.")

        # Stats row
        stats = ctk.CTkFrame(self.report_body, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 16))
        for i in range(4):
            stats.columnconfigure(i, weight=1)

        stat_data = [
            ("Invoices", str(report["count"]), COLORS["accent"]),
            ("Revenue", f"{currency} {report['total_revenue']:,.0f}", COLORS["success"]),
            ("Collected", f"{currency} {report['total_collected']:,.0f}", COLORS["success"]),
            ("Due", f"{currency} {report['total_due']:,.0f}", COLORS["warning"]),
        ]
        for i, (label, value, color) in enumerate(stat_data):
            c = Card(stats)
            c.grid(row=0, column=i, padx=(0 if i == 0 else 10), sticky="ew")
            AppLabel(c, label, style="label").pack(anchor="w", padx=14, pady=(12, 0))
            ctk.CTkLabel(c, text=value, font=FONT["heading_md"],
                         text_color=color).pack(anchor="w", padx=14, pady=(2, 12))

        # Invoices table
        AppLabel(self.report_body, "Invoices", style="heading_sm").pack(
            anchor="w", pady=(0, 8)
        )
        self._render_sales_table(self.report_body, report["sales"], currency)

    # ------------------------------------------------------------------
    # Monthly Report
    # ------------------------------------------------------------------

    def _show_monthly(self):
        self._set_active_tab("monthly")
        self._clear_scroll()

        ctrl = ctk.CTkFrame(self.scroll, fg_color="transparent")
        ctrl.pack(fill="x", pady=(0, 16))
        AppLabel(ctrl, "Month:", style="label_bold").pack(side="left")

        now = date.today()
        months = ["1 - Jan","2 - Feb","3 - Mar","4 - Apr","5 - May","6 - Jun",
                  "7 - Jul","8 - Aug","9 - Sep","10 - Oct","11 - Nov","12 - Dec"]
        # Initialize to the current month's full label so OptionMenu displays correctly
        current_month_label = next(m for m in months if m.startswith(str(now.month) + " "))
        self.month_var = tk.StringVar(value=current_month_label)
        self.year_var  = tk.StringVar(value=str(now.year))

        ctk.CTkOptionMenu(ctrl, values=months, width=130,
                          variable=self.month_var,
                          fg_color=COLORS["bg_input"],
                          button_color=COLORS["accent"],
                          dropdown_fg_color=COLORS["bg_card"],
                          text_color=COLORS["text_primary"],
                          font=FONT["body"],
                          ).pack(side="left", padx=(8, 0))

        AppEntry(ctrl, placeholder="Year", textvariable=self.year_var,
                 width=90).pack(side="left", padx=(8, 0))
        AppButton(ctrl, "Load", command=self._load_monthly,
                  style="primary", width=80, height=34).pack(side="left", padx=(8, 0))

        self.monthly_body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.monthly_body.pack(fill="x")
        self._load_monthly()

    def _load_monthly(self):
        for w in self.monthly_body.winfo_children():
            w.destroy()

        try:
            month = int(self.month_var.get().split(" ")[0])
            year  = int(self.year_var.get())
        except ValueError:
            AppLabel(self.monthly_body, "Invalid month/year.", style="body").pack()
            return

        report = business.monthly_sales_report(self.session, year, month)
        currency = business.get_setting(self.session, "currency", "Rs.")

        import calendar
        month_name = calendar.month_name[month]

        AppLabel(self.monthly_body, f"{month_name} {year}  —  Summary",
                 style="heading_sm").pack(anchor="w", pady=(0, 12))

        # Stats grid
        stats = ctk.CTkFrame(self.monthly_body, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 16))
        for i in range(4):
            stats.columnconfigure(i, weight=1)

        stat_data = [
            ("Total Invoices",  str(report["count"]),  COLORS["accent"]),
            ("Revenue",  f"{currency} {report['total_revenue']:,.0f}",  COLORS["accent"]),
            ("Gross Profit",  f"{currency} {report['gross_profit']:,.0f}",  COLORS["success"]),
            ("Outstanding Due",  f"{currency} {report['total_due']:,.0f}",  COLORS["warning"]),
        ]
        for i, (label, value, color) in enumerate(stat_data):
            c = Card(stats)
            c.grid(row=0, column=i, padx=(0 if i == 0 else 10), sticky="ew")
            AppLabel(c, label, style="label").pack(anchor="w", padx=14, pady=(12, 0))
            ctk.CTkLabel(c, text=value, font=FONT["heading_md"],
                         text_color=color).pack(anchor="w", padx=14, pady=(2, 12))

        # Top products
        if report["top_products"]:
            AppLabel(self.monthly_body, "Top Products by Quantity Sold",
                     style="heading_sm").pack(anchor="w", pady=(16, 8))
            card = Card(self.monthly_body)
            card.pack(fill="x", pady=(0, 16))
            for rank, (name, qty) in enumerate(report["top_products"], 1):
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=4)
                ctk.CTkLabel(row, text=f"{rank}.", font=FONT["label_bold"],
                             text_color=COLORS["text_muted"], width=24).pack(side="left")
                ctk.CTkLabel(row, text=name, font=FONT["body"],
                             text_color=COLORS["text_primary"]).pack(side="left", padx=(4, 0))
                ctk.CTkLabel(row, text=f"{qty:.0f} sold", font=FONT["body_sm"],
                             text_color=COLORS["text_secondary"]).pack(side="right")

        # All invoices
        AppLabel(self.monthly_body, "All Invoices", style="heading_sm").pack(
            anchor="w", pady=(8, 8)
        )
        self._render_sales_table(self.monthly_body, report["sales"], currency)

    # ------------------------------------------------------------------
    # Shared: Sales table
    # ------------------------------------------------------------------

    def _render_sales_table(self, parent, sales, currency):
        if not sales:
            ctk.CTkLabel(parent, text="No sales for this period.",
                         font=FONT["body"], text_color=COLORS["text_muted"]).pack(pady=16)
            return

        card = Card(parent)
        card.pack(fill="x")

        hdr = ctk.CTkFrame(card, fg_color="#F1F3F5", corner_radius=0)
        hdr.pack(fill="x")
        for text, width in [("Invoice", 130), ("Date", 130), ("Customer", 180),
                             ("Total", 110), ("Paid", 110), ("Due", 110), ("Status", 90)]:
            ctk.CTkLabel(hdr, text=text, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"],
                         width=width, anchor="w").pack(side="left", padx=8, pady=8)

        for s in sales:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x")
            Divider(card).pack(fill="x")

            for text, width, color in [
                (s.invoice_number, 130, COLORS["text_accent"]),
                (s.date.strftime("%d %b %Y"), 130, COLORS["text_secondary"]),
                (s.customer_name, 180, COLORS["text_primary"]),
                (f"{currency} {s.total:,.0f}", 110, COLORS["text_primary"]),
                (f"{currency} {s.amount_paid:,.0f}", 110, COLORS["success"]),
                (f"{currency} {s.amount_due:,.0f}", 110, COLORS["warning"]),
            ]:
                ctk.CTkLabel(row, text=text, font=FONT["body_sm"],
                             text_color=color, width=width, anchor="w").pack(
                    side="left", padx=8, pady=8)
            StatusBadge(row, s.status).pack(side="left", padx=4)
