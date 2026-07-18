"""
Settings Screen — shop info, password change.
"""

import customtkinter as ctk
import tkinter as tk
from theme import (
    COLORS, FONT, Card, AppButton, AppEntry, AppLabel,
    Divider, show_error, show_info
)
import business


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, parent, session, navigate):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.navigate = navigate
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        AppLabel(top, "Settings", style="heading_lg").pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 16))

        self._build_shop_info(scroll)
        self._build_password(scroll)
        self._build_backup_info(scroll)

    def _build_shop_info(self, parent):
        card = Card(parent)
        card.pack(fill="x", pady=(0, 16))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        AppLabel(inner, "Shop Information", style="heading_sm").pack(anchor="w", pady=(0, 16))
        AppLabel(inner, "This information appears on every printed invoice.", style="muted").pack(
            anchor="w", pady=(0, 16)
        )

        def row(label, key, placeholder=""):
            ctk.CTkLabel(inner, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(8, 2))
            var = tk.StringVar(value=business.get_setting(self.session, key, ""))
            AppEntry(inner, placeholder=placeholder, textvariable=var, width=500).pack(anchor="w")
            return var, key

        self.v_shop_name, _ = row("Shop Name", "shop_name", "Your shop name")
        self.v_address, _   = row("Address", "shop_address", "Shop address")
        self.v_phone, _     = row("Phone", "shop_phone", "Phone number")
        self.v_currency, _  = row("Currency Symbol", "currency", "Rs.")

        # Bind vars for save
        self._shop_fields = [
            (self.v_shop_name, "shop_name"),
            (self.v_address, "shop_address"),
            (self.v_phone, "shop_phone"),
            (self.v_currency, "currency"),
        ]

        AppButton(inner, "Save Shop Info", command=self._save_shop_info,
                  width=160, height=38).pack(anchor="w", pady=(16, 0))

    def _save_shop_info(self):
        for var, key in self._shop_fields:
            business.set_setting(self.session, key, var.get().strip())
        show_info(self, "Shop information saved successfully.")

    def _build_password(self, parent):
        card = Card(parent)
        card.pack(fill="x", pady=(0, 16))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        AppLabel(inner, "Change Password", style="heading_sm").pack(anchor="w", pady=(0, 16))

        def pw_row(label, placeholder):
            ctk.CTkLabel(inner, text=label, font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(8, 2))
            var = tk.StringVar()
            e = AppEntry(inner, placeholder=placeholder, textvariable=var, width=500)
            e.configure(show="●")
            e.pack(anchor="w")
            return var

        self.v_old_pw  = pw_row("Current Password", "Current password")
        self.v_new_pw  = pw_row("New Password", "New password (min 4 characters)")
        self.v_new_pw2 = pw_row("Confirm New Password", "Re-enter new password")

        AppButton(inner, "Change Password", command=self._change_password,
                  width=160, height=38).pack(anchor="w", pady=(16, 0))

    def _change_password(self):
        old  = self.v_old_pw.get()
        new  = self.v_new_pw.get()
        new2 = self.v_new_pw2.get()

        if not business.verify_login(self.session, old):
            show_error(self, "Current password is incorrect.")
            return
        if len(new) < 4:
            show_error(self, "New password must be at least 4 characters.")
            return
        if new != new2:
            show_error(self, "New passwords don't match.")
            return

        business.set_password(self.session, new)
        self.v_old_pw.set("")
        self.v_new_pw.set("")
        self.v_new_pw2.set("")
        show_info(self, "Password changed successfully.")

    def _build_backup_info(self, parent):
        card = Card(parent)
        card.pack(fill="x", pady=(0, 16))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        AppLabel(inner, "Backups", style="heading_sm").pack(anchor="w", pady=(0, 12))
        AppLabel(inner,
                 "A backup is automatically saved every time the app closes.\n"
                 "Backup files are stored in the 'backups' folder next to the app.\n\n"
                 "💡 Tip: Copy the entire app folder to a USB drive occasionally for extra safety.",
                 style="body").pack(anchor="w")

        AppButton(inner, "Backup Now", command=self._backup_now,
                  style="ghost", width=130, height=36).pack(anchor="w", pady=(16, 0))

    def _backup_now(self):
        from models import get_db_path
        from business import backup_database
        try:
            dest = backup_database(get_db_path())
            show_info(self, f"Backup saved to:\n{dest}")
        except Exception as e:
            show_error(self, f"Backup failed: {e}")
