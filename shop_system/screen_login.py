"""
Login Screen — light background, centered card, green accent.
Matches the new light theme.
"""

import customtkinter as ctk
import tkinter as tk
from theme import COLORS, FONT, AppButton, AppEntry, AppLabel
import business


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, session, on_success):
        super().__init__(parent, fg_color=COLORS["bg_base"])
        self.session = session
        self.on_success = on_success
        self._build()

    def _build(self):
        # Centered card
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.place(relx=0.5, rely=0.5, anchor="center")

        # Shadow-style card
        card = ctk.CTkFrame(outer,
                            fg_color=COLORS["bg_card"],
                            corner_radius=14,
                            border_width=1,
                            border_color=COLORS["border"])
        card.pack()

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=52, pady=48)

        # Logo pill
        logo = ctk.CTkFrame(inner,
                             fg_color=COLORS["accent"],
                             corner_radius=12,
                             width=56, height=56)
        logo.pack(pady=(0, 16))
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="🏪",
                     font=("Segoe UI Emoji", 26)).place(relx=0.5, rely=0.5, anchor="center")

        shop_name = business.get_setting(self.session, "shop_name", "My Shop")
        ctk.CTkLabel(inner, text=shop_name,
                     font=FONT["heading_xl"],
                     text_color=COLORS["text_primary"]).pack()
        ctk.CTkLabel(inner, text="Billing & Inventory System",
                     font=FONT["body"],
                     text_color=COLORS["text_muted"]).pack(pady=(2, 32))

        first_run = not business.is_password_set(self.session)

        if first_run:
            ctk.CTkLabel(inner,
                         text="Welcome! Set your admin password to get started.",
                         font=FONT["body"],
                         text_color=COLORS["text_secondary"],
                         wraplength=300).pack(pady=(0, 20))

        # Password field
        ctk.CTkLabel(inner, text="Password",
                     font=FONT["label_bold"],
                     text_color=COLORS["text_secondary"],
                     anchor="w").pack(fill="x")
        self.pw_var = tk.StringVar()
        self.pw_entry = AppEntry(inner, placeholder="Enter password", width=320)
        self.pw_entry.configure(show="●", textvariable=self.pw_var)
        self.pw_entry.pack(pady=(4, 0))
        self.pw_entry.bind("<Return>", lambda e: self._submit())

        self.confirm_entry = None
        if first_run:
            ctk.CTkLabel(inner, text="Confirm Password",
                         font=FONT["label_bold"],
                         text_color=COLORS["text_secondary"],
                         anchor="w").pack(fill="x", pady=(14, 0))
            self.confirm_var = tk.StringVar()
            self.confirm_entry = AppEntry(inner, placeholder="Re-enter password", width=320)
            self.confirm_entry.configure(show="●", textvariable=self.confirm_var)
            self.confirm_entry.pack(pady=(4, 0))
            self.confirm_entry.bind("<Return>", lambda e: self._submit())

        self.error_label = ctk.CTkLabel(inner, text="",
                                         font=FONT["body_sm"],
                                         text_color=COLORS["danger"])
        self.error_label.pack(pady=(10, 0))

        btn_text = "Set Password & Enter" if first_run else "Login"
        AppButton(inner, btn_text, command=self._submit,
                  width=320, height=44).pack(pady=(8, 0))

        self.pw_entry.focus()

    def _submit(self):
        pw = self.pw_var.get().strip()
        if not pw:
            self.error_label.configure(text="Password cannot be empty.")
            return

        first_run = not business.is_password_set(self.session)
        if first_run:
            confirm = self.confirm_var.get().strip()
            if pw != confirm:
                self.error_label.configure(text="Passwords don't match.")
                return
            if len(pw) < 4:
                self.error_label.configure(text="Password must be at least 4 characters.")
                return
            business.set_password(self.session, pw)
            self.on_success()
        else:
            if business.verify_login(self.session, pw):
                self.on_success()
            else:
                self.error_label.configure(text="Incorrect password. Try again.")
                self.pw_var.set("")
                self.pw_entry.focus()
