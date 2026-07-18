"""
Main Application Shell — dark navy sidebar + light content area.
Standard layout: QuickBooks / Zoho Books style.
"""

import customtkinter as ctk
import tkinter as tk
from theme import COLORS, FONT, AppButton
import business


NAV_ITEMS = [
    ("🏠", "Dashboard",   "dashboard"),
    ("🧾", "New Sale",    "billing"),
    ("📦", "Products",    "products"),
    ("📥", "Stock In",    "stock_in"),
    ("🔍", "Stock Check", "stock_check"),
    ("↩️",  "Returns",     "returns"),
    ("👥", "Customers",   "customers"),
    ("📊", "Reports",     "reports"),
    ("⚙️", "Settings",    "settings"),
]


class MainApp(ctk.CTkFrame):
    def __init__(self, parent, session):
        super().__init__(parent, fg_color=COLORS["bg_base"])
        self.session = session
        self.pack(fill="both", expand=True)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._screens  = {}
        self._active   = None
        self._nav_btns = {}

        self._build_sidebar()
        self._build_content()
        self.navigate("dashboard")

    # ------------------------------------------------------------------
    # Sidebar — dark navy
    # ------------------------------------------------------------------

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0,
            width=210,
        )
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.pack_propagate(False)
        sidebar.grid_propagate(False)

        # Right-edge border
        ctk.CTkFrame(sidebar, width=1,
                     fg_color=COLORS["sidebar_border"]).pack(side="right", fill="y")

        inner = ctk.CTkFrame(sidebar, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        # ---- Logo area ----
        logo_area = ctk.CTkFrame(inner, fg_color="transparent", height=80)
        logo_area.pack(fill="x")
        logo_area.pack_propagate(False)

        shop_name = business.get_setting(self.session, "shop_name", "My Shop")
        short_name = shop_name if len(shop_name) <= 15 else shop_name[:14] + "…"

        # Green accent pill for logo
        logo_pill = ctk.CTkFrame(logo_area,
                                  fg_color=COLORS["accent"],
                                  corner_radius=8,
                                  width=36, height=36)
        logo_pill.place(x=16, y=22)
        logo_pill.pack_propagate(False)
        ctk.CTkLabel(logo_pill, text="🏪",
                     font=("Segoe UI Emoji", 16)).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(logo_area, text=short_name,
                     font=FONT["heading_sm"],
                     text_color=COLORS["sidebar_text_active"]).place(x=60, y=24)
        ctk.CTkLabel(logo_area, text="Billing & Inventory",
                     font=FONT["label"],
                     text_color=COLORS["sidebar_text_muted"]).place(x=60, y=46)

        # Divider
        ctk.CTkFrame(inner, height=1,
                     fg_color=COLORS["sidebar_border"]).pack(fill="x")

        # Section label
        ctk.CTkLabel(inner, text="NAVIGATION",
                     font=("Segoe UI", 8, "bold"),
                     text_color=COLORS["sidebar_text_muted"]).pack(
            anchor="w", padx=16, pady=(12, 4))

        # Nav buttons
        nav_area = ctk.CTkFrame(inner, fg_color="transparent")
        nav_area.pack(fill="x", padx=8)

        for icon, label, key in NAV_ITEMS:
            btn = self._make_nav_btn(nav_area, icon, label, key)
            btn.pack(fill="x", pady=1)
            self._nav_btns[key] = btn

        # Bottom — version tag
        bottom = ctk.CTkFrame(inner, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=12, pady=12)
        ctk.CTkFrame(bottom, height=1,
                     fg_color=COLORS["sidebar_border"]).pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(bottom, text="v1.0  ·  Offline Mode",
                     font=FONT["label"],
                     text_color=COLORS["sidebar_text_muted"]).pack(anchor="w")

    def _make_nav_btn(self, parent, icon, label, key):
        return ctk.CTkButton(
            parent,
            text=f"  {icon}   {label}",
            font=FONT["nav_sm"],
            text_color=COLORS["sidebar_text"],
            fg_color="transparent",
            hover_color=COLORS["bg_sidebar_hover"],
            anchor="w",
            height=38,
            corner_radius=7,
            border_width=0,
            command=lambda k=key: self.navigate(k),
        )

    def _set_active_nav(self, key):
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["bg_sidebar_active"],
                    text_color=COLORS["sidebar_text_active"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["sidebar_text"],
                )

    # ------------------------------------------------------------------
    # Content area — light background
    # ------------------------------------------------------------------

    def _build_content(self):
        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_base"],
            corner_radius=0
        )
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

    def navigate(self, key: str):
        if self._active:
            self._active.grid_remove()

        # Dashboard always rebuilds for fresh data
        if key == "dashboard" and key in self._screens:
            self._screens[key].destroy()
            del self._screens[key]

        if key not in self._screens:
            self._screens[key] = self._build_screen(key)

        self._active = self._screens[key]
        self._active.grid(row=0, column=0, sticky="nsew")
        self._set_active_nav(key)

    def _build_screen(self, key: str):
        from screen_dashboard   import DashboardScreen
        from screen_billing     import BillingScreen
        from screen_products    import ProductsScreen
        from screen_stock_in    import StockInScreen
        from screen_stock_check import StockCheckScreen
        from screen_returns     import ReturnsScreen
        from screen_customers   import CustomersScreen
        from screen_reports     import ReportsScreen
        from screen_settings    import SettingsScreen

        s   = self.session
        nav = self.navigate

        builders = {
            "dashboard":   lambda: DashboardScreen(self.content, s, nav),
            "billing":     lambda: BillingScreen(self.content, s, nav),
            "products":    lambda: ProductsScreen(self.content, s, nav),
            "stock_in":    lambda: StockInScreen(self.content, s, nav),
            "stock_check": lambda: StockCheckScreen(self.content, s, nav),
            "returns":     lambda: ReturnsScreen(self.content, s, nav),
            "customers":   lambda: CustomersScreen(self.content, s, nav),
            "reports":     lambda: ReportsScreen(self.content, s, nav),
            "settings":    lambda: SettingsScreen(self.content, s, nav),
        }
        screen = builders[key]()
        screen.grid_configure(row=0, column=0, sticky="nsew")
        return screen
