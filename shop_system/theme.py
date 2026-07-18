"""
UI Theme — Light content, dark sidebar. 
Pattern used by: QuickBooks, Zoho Books, Shopify POS, Tally Prime.
Sidebar: deep navy  |  Content: warm white  |  Accent: forest green
This is the most readable combination for all-day data-entry use.
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------

COLORS = {
    # Sidebar — deep navy (Zoho/QuickBooks style)
    "bg_sidebar":      "#1B2A3B",   # main sidebar background
    "bg_sidebar_hover":"#243446",   # sidebar item hover
    "bg_sidebar_active":"#1A3A52",  # active nav item background
    "sidebar_border":  "#243446",   # right edge of sidebar

    # Content surfaces — warm whites, not cold blue-white
    "bg_base":         "#F4F5F7",   # main window / page background
    "bg_card":         "#FFFFFF",   # cards, panels
    "bg_input":        "#F8F9FA",   # input field background
    "bg_hover":        "#EFF1F4",   # table row hover
    "bg_selected":     "#E8F0FE",   # selected row

    # Accent — forest green (professional, readable, not neon)
    # Used by Zoho Books, Tally, and most South Asian billing software
    "accent":          "#1A7F5A",   # primary buttons, active states
    "accent_hover":    "#15694A",   # button hover
    "accent_dim":      "#E8F5EF",   # light tint for badges/backgrounds
    "accent_text":     "#1A7F5A",   # accent colored text

    # Semantic colors — clear but not garish
    "success":         "#1A7F5A",   # same as accent (paid, in stock)
    "success_dim":     "#E8F5EF",
    "warning":         "#B45309",   # amber — due balance, low stock
    "warning_dim":     "#FEF3C7",
    "danger":          "#B91C1C",   # red — error, delete, unpaid
    "danger_hover":    "#991B1B",
    "danger_dim":      "#FEE2E2",

    # Text — on light background
    "text_primary":    "#111827",   # near-black for main content
    "text_secondary":  "#4B5563",   # secondary labels
    "text_muted":      "#9CA3AF",   # placeholders, hints
    "text_accent":     "#1A7F5A",   # links, invoice numbers

    # Sidebar text (on dark background)
    "sidebar_text":    "#CBD5E1",   # normal nav items
    "sidebar_text_active": "#FFFFFF", # active nav item text
    "sidebar_text_muted":  "#64748B", # muted sidebar text

    # Borders
    "border":          "#E5E7EB",   # standard border
    "border_focus":    "#1A7F5A",   # focused input
    "border_card":     "#E5E7EB",

    # Compat aliases kept for existing screen references
    "bg_dark":         "#1B2A3B",
    "accent_light":    "#E8F5EF",
}

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

FONT = {
    "heading_xl":  ("Segoe UI", 22, "bold"),
    "heading_lg":  ("Segoe UI", 17, "bold"),
    "heading_md":  ("Segoe UI", 14, "bold"),
    "heading_sm":  ("Segoe UI", 12, "bold"),
    "body_lg":     ("Segoe UI", 13),
    "body":        ("Segoe UI", 12),
    "body_sm":     ("Segoe UI", 11),
    "mono":        ("Consolas", 11),
    "label":       ("Segoe UI", 10),
    "label_bold":  ("Segoe UI", 10, "bold"),
    "nav":         ("Segoe UI", 12, "bold"),
    "nav_sm":      ("Segoe UI", 12),
}

# ---------------------------------------------------------------------------
# Global appearance — LIGHT mode
# ---------------------------------------------------------------------------

def setup_theme():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------

class AppButton(ctk.CTkButton):
    STYLES = {
        "primary": ("#1A7F5A", "#15694A", "#FFFFFF"),
        "success": ("#1A7F5A", "#15694A", "#FFFFFF"),
        "danger":  ("#B91C1C", "#991B1B", "#FFFFFF"),
        "ghost":   ("#F4F5F7", "#E5E7EB", "#4B5563"),
        "neutral": ("#FFFFFF",  "#F4F5F7", "#4B5563"),
    }

    def __init__(self, parent, text, command=None, style="primary",
                 width=120, height=36, **kwargs):
        fg, hover, txt = self.STYLES.get(style, self.STYLES["primary"])
        super().__init__(
            parent, text=text, command=command,
            fg_color=fg, hover_color=hover,
            text_color=txt,
            font=FONT["body_lg"],
            corner_radius=7,
            width=width, height=height,
            border_width=0,
            **kwargs
        )


class IconButton(ctk.CTkButton):
    STYLES = {
        "ghost":   ("#F4F5F7", "#E5E7EB", "#4B5563"),
        "danger":  ("#FEE2E2", "#FECACA", "#B91C1C"),
        "success": ("#E8F5EF", "#D1FAE5", "#1A7F5A"),
        "primary": ("#E8F0FE", "#DBEAFE", "#1A7F5A"),
    }

    def __init__(self, parent, text, command=None, style="ghost", **kwargs):
        fg, hover, txt = self.STYLES.get(style, self.STYLES["ghost"])
        super().__init__(
            parent, text=text, command=command,
            fg_color=fg, hover_color=hover,
            text_color=txt,
            font=FONT["body_sm"],
            corner_radius=6,
            width=68, height=26,
            border_width=0,
            **kwargs
        )


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

class AppEntry(ctk.CTkEntry):
    def __init__(self, parent, placeholder="", width=200, **kwargs):
        super().__init__(
            parent,
            placeholder_text=placeholder,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            font=FONT["body_lg"],
            corner_radius=7,
            border_width=1,
            width=width,
            **kwargs
        )
        self.bind("<FocusIn>",  lambda e: self.configure(border_color=COLORS["border_focus"]))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=COLORS["border"]))


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

class AppLabel(ctk.CTkLabel):
    _MAP = {
        "heading_xl": ("heading_xl", "text_primary"),
        "heading_lg": ("heading_lg", "text_primary"),
        "heading_md": ("heading_md", "text_primary"),
        "heading_sm": ("heading_sm", "text_primary"),
        "body_lg":    ("body_lg",    "text_primary"),
        "body":       ("body",       "text_primary"),
        "body_sm":    ("body_sm",    "text_secondary"),
        "label":      ("label",      "text_secondary"),
        "label_bold": ("label_bold", "text_secondary"),
        "muted":      ("body_sm",    "text_muted"),
    }

    def __init__(self, parent, text, style="body", **kwargs):
        fk, ck = self._MAP.get(style, ("body", "text_primary"))
        super().__init__(
            parent, text=text,
            font=FONT[fk],
            text_color=COLORS[ck],
            **kwargs
        )


# ---------------------------------------------------------------------------
# Containers
# ---------------------------------------------------------------------------

class Card(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border_card"],
            **kwargs
        )


class Divider(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=1, fg_color=COLORS["border"], **kwargs)


class SectionHeader(ctk.CTkFrame):
    def __init__(self, parent, title, subtitle="", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        AppLabel(self, text=title, style="heading_lg").pack(anchor="w")
        if subtitle:
            AppLabel(self, text=subtitle, style="muted").pack(anchor="w", pady=(2, 0))


# ---------------------------------------------------------------------------
# Status Badge
# ---------------------------------------------------------------------------

class StatusBadge(ctk.CTkLabel):
    _COLORS = {
        "paid":    ("#E8F5EF", "#1A7F5A"),
        "partial": ("#FEF3C7", "#B45309"),
        "unpaid":  ("#FEE2E2", "#B91C1C"),
        "low":     ("#FEF3C7", "#B45309"),
        "ok":      ("#E8F5EF", "#1A7F5A"),
    }

    def __init__(self, parent, status: str, **kwargs):
        bg, fg = self._COLORS.get(status.lower(), (COLORS["bg_input"], COLORS["text_secondary"]))
        super().__init__(
            parent, text=status.upper(),
            fg_color=bg, text_color=fg,
            font=FONT["label_bold"],
            corner_radius=5,
            padx=8, pady=2,
            **kwargs
        )


# ---------------------------------------------------------------------------
# Search Bar
# ---------------------------------------------------------------------------

class SearchBar(ctk.CTkFrame):
    def __init__(self, parent, placeholder="Search...", on_change=None, width=280, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_change = on_change
        self.var = tk.StringVar()
        self.var.trace_add("write", self._on_change)

        self.entry = AppEntry(self, placeholder=placeholder, width=width, textvariable=self.var)
        self.entry.pack(side="left")

        self.clear_btn = ctk.CTkButton(
            self, text="✕", width=30, height=36,
            fg_color=COLORS["bg_input"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"], font=FONT["body"],
            corner_radius=7, command=self.clear, border_width=1,
            border_color=COLORS["border"]
        )
        self.clear_btn.pack(side="left", padx=(3, 0))

    def _on_change(self, *_):
        if self.on_change:
            self.on_change(self.var.get())

    def clear(self):
        self.var.set("")

    def get(self):
        return self.var.get()


# ---------------------------------------------------------------------------
# Stat Card (Dashboard)
# ---------------------------------------------------------------------------

class StatCard(ctk.CTkFrame):
    def __init__(self, parent, label, value, sub="", accent_color=None, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border_card"],
            **kwargs
        )
        color = accent_color or COLORS["text_primary"]
        ctk.CTkLabel(self, text=label,
                     font=FONT["label_bold"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=16, pady=(14, 0))
        ctk.CTkLabel(self, text=str(value),
                     font=FONT["heading_xl"],
                     text_color=color).pack(anchor="w", padx=16, pady=(3, 0))
        if sub:
            ctk.CTkLabel(self, text=sub,
                         font=FONT["body_sm"],
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=16, pady=(1, 14))
        else:
            ctk.CTkFrame(self, height=14, fg_color="transparent").pack()


# ---------------------------------------------------------------------------
# Modal Base
# ---------------------------------------------------------------------------

class ModalDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, width=480, height=400):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.configure(fg_color=COLORS["bg_base"])
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - width  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - height // 2
        self.geometry(f"{width}x{height}+{px}+{py}")

    def _header(self, title):
        f = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                         corner_radius=0, height=52,
                         border_width=0)
        f.pack(fill="x")
        f.pack_propagate(False)
        # Bottom border line
        ctk.CTkFrame(f, height=1, fg_color=COLORS["border"]).pack(side="bottom", fill="x")
        ctk.CTkLabel(f, text=title, font=FONT["heading_md"],
                     text_color=COLORS["text_primary"]).pack(side="left", padx=20, pady=14)
        return f

    def _footer(self, on_cancel=None, on_confirm=None,
                cancel_text="Cancel", confirm_text="Save", confirm_style="primary"):
        f = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                         corner_radius=0, height=56, border_width=0)
        f.pack(fill="x", side="bottom")
        f.pack_propagate(False)
        # Top border line
        ctk.CTkFrame(f, height=1, fg_color=COLORS["border"]).pack(side="top", fill="x")
        if on_cancel:
            AppButton(f, cancel_text, command=on_cancel, style="ghost",
                      width=90, height=32).pack(side="right", padx=(0, 8), pady=12)
        if on_confirm:
            AppButton(f, confirm_text, command=on_confirm, style=confirm_style,
                      width=110, height=32).pack(side="right", padx=(0, 4), pady=12)
        return f


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def confirm_dialog(parent, title, message) -> bool:
    return messagebox.askyesno(title, message, parent=parent)

def show_error(parent, message):
    messagebox.showerror("Error", message, parent=parent)

def show_info(parent, message, title="Done"):
    messagebox.showinfo(title, message, parent=parent)
