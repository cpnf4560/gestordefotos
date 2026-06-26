"""Main menu screen for choosing which application to run."""

import tkinter as tk
from tkinter import ttk

from premium_theme import configure_premium_theme, CARD, CARD_BORDER, BG_ALT, WHITE, ACCENT, ACCENT_2, WARN


class MenuScreen:
    """Main menu to choose functionality."""

    def __init__(self, root: tk.Tk):
        self.root = root
        configure_premium_theme(self.root)
        self.root.title("Gestor de Fotos")
        self.root.geometry("980x720")
        self.root.minsize(920, 660)
        self.root.configure(bg="#0f172a")
        self.root.resizable(False, False)

        self.selected = None
        self._cards = []
        self._create_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

    def _create_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TFrame", background="#0f172a")
        style.configure("Dark.TLabel", background="#0f172a", foreground="#e2e8f0")
        style.configure("Title.TLabel", background="#0f172a", foreground="#f8fafc", font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", background="#0f172a", foreground="#cbd5e1", font=("Segoe UI", 11))
        style.configure("CardTitle.TLabel", background="#111827", foreground="#f8fafc", font=("Segoe UI", 14, "bold"))
        style.configure("CardBody.TLabel", background="#111827", foreground="#cbd5e1", font=("Segoe UI", 10), wraplength=250)
        style.configure("CardAction.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8))

        outer = ttk.Frame(self.root, style="Dark.TFrame")
        outer.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(outer, bg="#0f172a")
        header.pack(fill=tk.X, padx=36, pady=(28, 18))

        badge = tk.Label(
            header,
            text="Gestão de fotos",
            bg="#1e293b",
            fg="#93c5fd",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=6,
        )
        badge.pack(anchor=tk.W)

        title = ttk.Label(header, text="Gestor de Fotos", style="Title.TLabel")
        title.pack(anchor=tk.W, pady=(14, 4))

        subtitle = ttk.Label(
            header,
            text="Escolhe a aplicação pretendida. Cada módulo é independente e pensado para um fluxo específico.",
            style="Subtitle.TLabel",
        )
        subtitle.pack(anchor=tk.W)

        cards_wrap = tk.Frame(outer, bg="#0f172a")
        cards_wrap.pack(fill=tk.BOTH, expand=True, padx=36, pady=12)
        cards_wrap.grid_columnconfigure(0, weight=1)
        cards_wrap.grid_columnconfigure(1, weight=1)
        cards_wrap.grid_columnconfigure(2, weight=1)

        quick_row = tk.Frame(outer, bg="#0f172a")
        quick_row.pack(fill=tk.X, padx=36, pady=(0, 4))

        quick_tags = [
            ("Sem clutter", "Tudo numa janela", ACCENT),
            ("Teclado", "Navegação rápida", ACCENT_2),
            ("Testes", "Log em logs/app.log", WARN),
        ]
        for title_text, body_text, color in quick_tags:
            pill = tk.Frame(quick_row, bg="#111827", highlightthickness=1, highlightbackground=color)
            pill.pack(side=tk.LEFT, padx=6, pady=2)
            tk.Label(pill, text=title_text, bg="#111827", fg=WHITE, font=("Segoe UI", 9, "bold"), padx=10, pady=4).pack()
            tk.Label(pill, text=body_text, bg="#111827", fg="#cbd5e1", font=("Segoe UI", 8), padx=10, pady=4).pack()

        self._create_card(
            cards_wrap,
            row=0,
            column=0,
            accent="#38bdf8",
            icon="🔍",
            title="Procurar repetidos",
            body="Compara por conteúdo visual, MD5, dimensões e metadados.\n\nIdeal para limpar bibliotecas grandes e escolher rapidamente qual imagem manter.",
            action_text="Abrir procurador",
            option="duplicates",
        )
        self._create_card(
            cards_wrap,
            row=0,
            column=1,
            accent="#34d399",
            icon="📅",
            title="Editar data das fotos",
            body="Corrige datas EXIF de fotos digitalizadas ou de ficheiros com data errada.\n\nSuporta ano apenas, datas completas e edição em lote.",
            action_text="Abrir editor",
            option="exif_editor",
        )
        self._create_card(
            cards_wrap,
            row=0,
            column=2,
            accent="#f59e0b",
            icon="⚙️",
            title="Ferramentas em lote",
            body="Renomear, redimensionar e organizar por data.\n\nÚtil para manutenção da biblioteca e preparação para partilha.",
            action_text="Abrir ferramentas",
            option="batch_tools",
        )

        footer = tk.Frame(outer, bg="#0b1220", height=56)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        footer_left = tk.Frame(footer, bg="#0b1220")
        footer_left.pack(side=tk.LEFT, padx=24, pady=10)

        tk.Label(
            footer_left,
            text="v1.0",
            bg="#0b1220",
            fg="#cbd5e1",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=tk.W)

        tk.Label(
            footer_left,
            text="Carlos Correia 2026 - Todos os direitos reservados",
            bg="#0b1220",
            fg="#94a3b8",
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W)

        footer_right = tk.Frame(footer, bg="#0b1220")
        footer_right.pack(side=tk.RIGHT, padx=24, pady=10)
        ttk.Button(footer_right, text="Sair", style="CardAction.TButton", command=self.root.quit).pack()

    def _create_card(self, parent, row, column, accent, icon, title, body, action_text, option):
        container = tk.Frame(parent, bg="#111827", highlightthickness=1, highlightbackground="#1f2937")
        container.grid(row=row, column=column, sticky="nsew", padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.configure(cursor="hand2")

        accent_bar = tk.Frame(container, bg=accent, height=7)
        accent_bar.grid(row=0, column=0, sticky="ew")

        body_frame = tk.Frame(container, bg="#111827")
        body_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)

        icon_label = tk.Label(body_frame, text=icon, bg="#111827", fg="#f8fafc", font=("Segoe UI", 28))
        icon_label.pack(anchor=tk.W)

        ttk.Label(body_frame, text=title, style="CardTitle.TLabel").pack(anchor=tk.W, pady=(10, 8))
        ttk.Label(body_frame, text=body, style="CardBody.TLabel").pack(anchor=tk.W)

        button = ttk.Button(body_frame, text=action_text, style="CardAction.TButton", command=lambda: self._select_option(option))
        button.pack(anchor=tk.W, pady=(18, 0))

        for widget in (container, accent_bar, body_frame, icon_label):
            widget.bind("<Button-1>", lambda _event, value=option: self._select_option(value))
            widget.bind("<Enter>", lambda _event, card=container: self._set_card_hover(card, True))
            widget.bind("<Leave>", lambda _event, card=container: self._set_card_hover(card, False))

        for child in body_frame.winfo_children():
            try:
                child.bind("<Button-1>", lambda _event, value=option: self._select_option(value))
                child.bind("<Enter>", lambda _event, card=container: self._set_card_hover(card, True))
                child.bind("<Leave>", lambda _event, card=container: self._set_card_hover(card, False))
            except Exception:
                pass

        self._cards.append(container)

    def _set_card_hover(self, card: tk.Frame, hover: bool):
        card.configure(highlightbackground=ACCENT if hover else CARD_BORDER, highlightthickness=2 if hover else 1)

    def _select_option(self, option: str):
        self.selected = option
        self.root.quit()


def show_menu(root: tk.Tk = None):
    """Show main menu on existing root and return selected option."""
    if root is None:
        root = tk.Tk()
    for widget in root.winfo_children():
        widget.destroy()
    root.resizable(True, True)
    root.deiconify()
    menu = MenuScreen(root)
    root.protocol("WM_DELETE_WINDOW", root.quit)  # X button = quit mainloop, not destroy
    root.mainloop()
    root.protocol("WM_DELETE_WINDOW", "")  # reset
    return menu.selected


if __name__ == "__main__":
    option = show_menu()
    print(f"Selected: {option}")
