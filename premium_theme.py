"""Shared premium theme helpers for the application UI."""

import tkinter as tk
from tkinter import ttk

BG = "#0f172a"
BG_ALT = "#111827"
BG_PANEL = "#0b1220"
CARD = "#111827"
CARD_BORDER = "#1f2937"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
ACCENT_2 = "#34d399"
WARN = "#f59e0b"
DANGER = "#ef4444"
WHITE = "#f8fafc"


def configure_premium_theme(root: tk.Tk):
    """Apply a consistent premium dark theme to a window."""
    root.configure(bg=BG)
    root.option_add("*Background", BG)
    root.option_add("*Foreground", TEXT)
    root.option_add("*activeBackground", BG_ALT)
    root.option_add("*activeForeground", WHITE)
    root.option_add("*highlightBackground", CARD_BORDER)
    root.option_add("*selectBackground", ACCENT)
    root.option_add("*selectForeground", BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("TLabelframe", background=BG_ALT, foreground=WHITE)
    style.configure("TLabelframe.Label", background=BG_ALT, foreground=WHITE, font=("Segoe UI", 10, "bold"))
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
    style.configure("Horizontal.TProgressbar", troughcolor=BG_ALT, background=ACCENT, bordercolor=BG_ALT, lightcolor=ACCENT, darkcolor=ACCENT)
    style.configure("Vertical.TScrollbar", background=BG_ALT, troughcolor=BG_ALT, arrowcolor=TEXT)
    style.configure("Horizontal.TScrollbar", background=BG_ALT, troughcolor=BG_ALT, arrowcolor=TEXT)
    style.configure("Treeview", background=BG_ALT, fieldbackground=BG_ALT, foreground=TEXT, rowheight=28, bordercolor=BG_ALT)
    style.configure("Treeview.Heading", background=CARD_BORDER, foreground=WHITE, font=("Segoe UI", 10, "bold"))
    style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", BG)])

    style.configure("Premium.TFrame", background=BG)
    style.configure("PremiumAlt.TFrame", background=BG_ALT)
    style.configure("Panel.TFrame", background=BG_PANEL)
    style.configure("Card.TFrame", background=CARD)
    style.configure("CardBorder.TFrame", background=CARD_BORDER)
    style.configure("Premium.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
    style.configure("Title.TLabel", background=BG, foreground=WHITE, font=("Segoe UI", 22, "bold"))
    style.configure("Subtitle.TLabel", background=BG, foreground="#cbd5e1", font=("Segoe UI", 11))
    style.configure("CardTitle.TLabel", background=CARD, foreground=WHITE, font=("Segoe UI", 14, "bold"))
    style.configure("CardBody.TLabel", background=CARD, foreground="#cbd5e1", font=("Segoe UI", 10), wraplength=260)
    style.configure("Premium.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
    style.configure("CardAction.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8))
    style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8), foreground=WHITE)
    style.map("Danger.TButton", background=[("active", DANGER), ("!disabled", DANGER)], foreground=[("!disabled", WHITE)])
    style.configure("Premium.Horizontal.TProgressbar", troughcolor=BG_ALT, background=ACCENT, bordercolor=BG_ALT, lightcolor=ACCENT, darkcolor=ACCENT)
    style.configure("Premium.Vertical.TScrollbar", background=BG_ALT, troughcolor=BG_ALT, arrowcolor=TEXT)
    style.configure("Premium.Horizontal.TScrollbar", background=BG_ALT, troughcolor=BG_ALT, arrowcolor=TEXT)
    style.configure("Premium.Treeview", background=BG_ALT, fieldbackground=BG_ALT, foreground=TEXT, rowheight=28, bordercolor=BG_ALT)
    style.configure("Premium.Treeview.Heading", background=CARD_BORDER, foreground=WHITE, font=("Segoe UI", 10, "bold"))
    style.map("Premium.Treeview", background=[("selected", ACCENT)], foreground=[("selected", BG)])
    return style


def make_card(parent, accent: str):
    """Create a premium card container with a colored accent bar."""
    container = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=CARD_BORDER)
    accent_bar = tk.Frame(container, bg=accent, height=7)
    accent_bar.pack(fill=tk.X, side=tk.TOP)
    content = tk.Frame(container, bg=CARD)
    content.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
    return container, content
