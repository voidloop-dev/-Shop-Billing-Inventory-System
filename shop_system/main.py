"""
Shop Billing & Inventory System — Entry Point
Double-click this (or the .exe) to start.
"""

import sys
import os

# Ensure the app folder is in the import path when running as .exe
if getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from theme import setup_theme, COLORS
from models import init_db, get_db_path
from business import backup_database

import tkinter as tk


class ShopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Shop Billing & Inventory")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.configure(fg_color=COLORS["bg_base"])

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 1280) // 2
        y = (sh - 780) // 2
        self.geometry(f"1280x780+{x}+{y}")

        setup_theme()

        # Init DB
        self.engine = init_db()
        from models import get_session
        self.session = get_session(self.engine)

        # Crash handler
        self.report_callback_exception = self._on_exception

        # Backup on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start with login screen
        self._show_login()

    def _show_login(self):
        self._clear()
        from screen_login import LoginScreen
        LoginScreen(self, self.session, on_success=self._show_main).pack(
            fill="both", expand=True
        )

    def _show_main(self):
        self._clear()
        from main_app import MainApp
        MainApp(self, self.session)

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _on_close(self):
        try:
            backup_database(get_db_path())
        except Exception:
            pass   # never block the close
        try:
            self.session.close()
        except Exception:
            pass
        self.destroy()

    def _on_exception(self, exc, val, tb):
        import traceback
        import logging
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error.log")
        logging.basicConfig(filename=log_path, level=logging.ERROR)
        logging.error("Unhandled exception", exc_info=(exc, val, tb))
        from tkinter import messagebox
        messagebox.showerror(
            "Something went wrong",
            "An unexpected error occurred.\n"
            "Your data is safe — please restart the app.\n\n"
            f"Details saved to error.log."
        )


if __name__ == "__main__":
    app = ShopApp()
    app.mainloop()
