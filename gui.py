"""
GUI for image duplicate viewer and management.
Displays duplicates side-by-side with similarity info and delete controls.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from pathlib import Path
from typing import List, Dict, Tuple
import threading
import logging

from image_scanner import ImageScanner, ImageInfo
from premium_theme import BG, BG_ALT, BG_PANEL, CARD, ACCENT, DANGER, WHITE, configure_premium_theme

logger = logging.getLogger(__name__)


class ImageDuplicateGUI:
    """Main GUI window for viewing and managing duplicate images."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        configure_premium_theme(self.root)
        self.root.title("Gestor de Fotos — Imagens Repetidas")
        self.root.geometry("1400x900")
        
        self.scanner: ImageScanner = None
        self.duplicates: Dict = {}
        self.current_group_idx = 0
        self.current_group_key = None
        self.marked_for_deletion: set = set()  # {file_path, ...}
        self.visible_slots = 0
        self.hotkey_hint_text = tk.StringVar(value="")
        self._photo_refs: list = []  # Strong references to prevent GC
        self.go_back_to_menu = False
        
        self._create_ui()
        
    def _create_ui(self):
        """Create main UI components."""
        # Top frame: controls
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(top_frame, text="📁 Selecionar Pasta", 
                  command=self._select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="🔍 Digitalizar", 
                  command=self._start_scan).pack(side=tk.LEFT, padx=5)
        
        self.scan_label = ttk.Label(top_frame, text="Nenhuma pasta selecionada")
        self.scan_label.pack(side=tk.LEFT, padx=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(top_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=10)

        ttk.Button(top_frame, text="🏠 Menu",
                  command=self._go_to_menu).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Sobre",
                  command=self._show_about).pack(side=tk.RIGHT, padx=2)
        
        # Middle frame: info and navigation
        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.info_label = ttk.Label(info_frame, text="")
        self.info_label.pack(side=tk.LEFT)

        nav_frame = ttk.Frame(info_frame)
        nav_frame.pack(side=tk.RIGHT)

        ttk.Button(nav_frame, text="⬅ Anterior",
                  command=self._prev_group).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Próximo ➡",
                  command=self._next_group).pack(side=tk.LEFT, padx=2)

        # Main content frame
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Welcome placeholder (shown before scan)
        self.welcome_frame = tk.Frame(self.content_frame, bg=BG)
        self.welcome_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        tk.Label(self.welcome_frame, text="🔍", font=("Segoe UI Emoji", 56),
                 bg=BG, fg="#334155").place(relx=0.5, rely=0.35, anchor="center")
        tk.Label(self.welcome_frame,
                 text="Seleciona uma pasta e clica em Digitalizar",
                 font=("Segoe UI", 14), bg=BG, fg="#475569").place(relx=0.5, rely=0.48, anchor="center")
        tk.Label(self.welcome_frame,
                 text="As imagens repetidas aparecerão aqui",
                 font=("Segoe UI", 10), bg=BG, fg="#334155").place(relx=0.5, rely=0.55, anchor="center")

        self.image_frames = []
        slot_positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, (row, column) in enumerate(slot_positions):
            frame = ttk.LabelFrame(self.content_frame, text="", width=400, height=450)
            frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
            self.content_frame.grid_rowconfigure(row, weight=1)
            self.content_frame.grid_columnconfigure(column, weight=1)
            
            # Image container with delete button overlay
            img_container = tk.Frame(frame, bg=BG_ALT)
            img_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            img_label = tk.Label(img_container, bg=BG_ALT)
            img_label.pack(fill=tk.BOTH, expand=True)
            img_label.bind("<Button-1>", lambda e, idx=i: self._toggle_delete(idx))
            img_container.bind("<Button-1>", lambda e, idx=i: self._toggle_delete(idx))
            
            # Delete button (appears on top right when marked)
            delete_btn = tk.Label(
                img_container,
                text="✕",
                font=("Arial", 24, "bold"),
                fg=DANGER,
                bg=WHITE,
                width=3,
                height=1,
                cursor="hand2"
            )
            delete_btn.place(relx=0.95, rely=0.05, anchor="ne")
            delete_btn.bind("<Button-1>", lambda e, idx=i: self._toggle_delete(idx))
            
            # File path label
            path_label = ttk.Label(frame, text="", justify=tk.LEFT, wraplength=350, foreground=ACCENT)
            path_label.pack(fill=tk.X, padx=5, pady=2)
            
            # Info label
            info_label = ttk.Label(frame, text="", justify=tk.LEFT, wraplength=350)
            info_label.pack(fill=tk.X, padx=5, pady=5)
            
            self.image_frames.append({
                'frame': frame,
                'container': img_container,
                'label': img_label,
                'delete_btn': delete_btn,
                'path_label': path_label,
                'info': info_label,
                'path': None
            })
        
        self.root.bind("<Left>", lambda e: self._prev_group())
        self.root.bind("<Right>", lambda e: self._next_group())
        self.root.bind("<Delete>", lambda e: self._delete_selected())
        for i in range(1, 5):
            self.root.bind(str(i), lambda e, idx=i-1: self._toggle_delete(idx))
        
        # Bottom frame: action buttons
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(bottom_frame, text="🗑 Eliminar Marcadas (🔴)", 
                  command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(bottom_frame, text="(Clique no ✕ vermelho para marcar)", 
             foreground="#94a3b8").pack(side=tk.LEFT, padx=10)
        
        ttk.Label(bottom_frame, textvariable=self.hotkey_hint_text, foreground="#94a3b8").pack(side=tk.LEFT, padx=10)
        
        ttk.Label(bottom_frame, text="  |  ← → = navegar grupos  •  1-4 = marcar foto  •  Del = eliminar",
             foreground="#64748b").pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(bottom_frame, text="", foreground="blue")
        self.status_label.pack(side=tk.RIGHT, padx=5)
    
    def _select_folder(self):
        """Open folder selection dialog."""
        folder = filedialog.askdirectory(title="Selecione a pasta com imagens")
        if folder:
            logger.info("Selected duplicate scan folder: %s", folder)
            self.scanner = ImageScanner(folder)
            self.scan_label.config(text=f"Pasta: {Path(folder).name}")
            self.duplicates = {}
            self.current_group_idx = 0
    
    def _start_scan(self):
        """Start image scanning in background thread."""
        if not self.scanner:
            messagebox.showwarning("Aviso", "Selecione uma pasta primeiro!")
            return
        
        logger.info("Starting duplicate scan")
        self.progress.start()
        self.scan_label.config(text="A digitalizar...")
        
        thread = threading.Thread(target=self._scan_worker)
        thread.daemon = True
        thread.start()
    
    def _scan_worker(self):
        """Worker thread for scanning."""
        try:
            self.scanner.scan(use_cache=True)
            self.duplicates = self.scanner.find_duplicates(similarity_threshold=0.85)
            self.current_group_idx = 0
            
            if not self.duplicates:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Resultado", f"Encontradas {len(self.scanner.images)} imagens, nenhuma duplicada!"
                ))
            else:
                total_dupes = sum(len(g['images']) for g in self.duplicates.values())
                self.root.after(0, lambda: messagebox.showinfo(
                    "Resultado", 
                    f"Encontradas {len(self.scanner.images)} imagens\n"
                    f"{len(self.duplicates)} grupos de duplicatas\n"
                    f"{total_dupes} imagens duplicadas no total"
                ))
            
            self.root.after(0, self._display_group)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao digitalizar: {str(e)}"))
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.scan_label.config(text="Digitalização completa"))
    
    def _display_group(self):
        """Display current duplicate group."""
        if not self.duplicates:
            for frame_data in self.image_frames:
                frame_data['label'].config(image='')
                frame_data['path_label'].config(text="")
                frame_data['info'].config(text="")
                frame_data['delete_btn'].config(relief=tk.FLAT, bg=WHITE, fg=DANGER)
                frame_data['path'] = None
            self.info_label.config(text="Nenhuma duplicata para exibir")
            self.welcome_frame.lift()  # show placeholder
            return

        self.welcome_frame.lower()  # hide placeholder
        group_keys = list(self.duplicates.keys())
        if self.current_group_idx >= len(group_keys):
            self.current_group_idx = 0
        
        self.current_group_key = group_keys[self.current_group_idx]
        group = self.duplicates[self.current_group_key]
        images = group['images']
        visible_count = max(2, min(len(images), len(self.image_frames)))
        self.visible_slots = visible_count
        
        # Update info
        group_type = group['type']
        similarity = group['similarity']
        self.info_label.config(
            text=f"Grupo {self.current_group_idx + 1}/{len(group_keys)} | "
                 f"Tipo: {group_type} | Similaridade: {similarity:.1%} | "
                 f"Mostrando {visible_count} imagem(ns)"
        )
        self._update_hotkey_hint(visible_count)
        self._layout_visible_slots(visible_count)
        
        # Display images
        for idx, frame_data in enumerate(self.image_frames):
            if idx < len(images):
                img_info = images[idx]
                self._load_image_preview(frame_data, img_info)
            else:
                frame_data['label'].config(image='')
                frame_data['label'].image = None
                frame_data['path_label'].config(text="")
                frame_data['info'].config(text="")
                frame_data['delete_btn'].config(relief=tk.FLAT, bg=WHITE, fg=DANGER)
                frame_data['path'] = None
                frame_data['frame'].grid_remove()
        
    def _layout_visible_slots(self, visible_count: int):
        """Show only the slots needed for the current group size."""
        for idx, frame_data in enumerate(self.image_frames):
            if idx < visible_count:
                frame_data['frame'].grid()
            else:
                frame_data['frame'].grid_remove()
        
        if visible_count <= 2:
            self.image_frames[0]['frame'].grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.image_frames[1]['frame'].grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        elif visible_count == 3:
            self.image_frames[0]['frame'].grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.image_frames[1]['frame'].grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
            self.image_frames[2]['frame'].grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        else:
            positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
            for idx, (row, column) in enumerate(positions):
                self.image_frames[idx]['frame'].grid(row=row, column=column, sticky="nsew", padx=5, pady=5)

    def _update_hotkey_hint(self, visible_count: int):
        slots = " | ".join(f"{i+1} = foto {i+1}" for i in range(visible_count))
        self.hotkey_hint_text.set(f"Marcar: {slots}")

    def _load_image_preview(self, frame_data: Dict, img_info: ImageInfo):
        """Load and display image preview."""
        try:
            img = Image.open(img_info.path)
            img.load()  # Force full pixel load before anything else (prevents lazy-load Tcl errors)
            
            # Always convert to a safe mode for ImageTk
            if img.mode == 'RGBA':
                img = img.copy()  # detach from file
            else:
                img = img.convert('RGB')
            
            # Resize for preview (max 350x350)
            img.thumbnail((350, 350), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Keep strong reference at class level AND widget level
            self._photo_refs.append(photo)
            if len(self._photo_refs) > 20:  # trim old references
                self._photo_refs = self._photo_refs[-20:]
            
            frame_data['label'].config(image=photo)
            frame_data['label'].image = photo  # Keep reference
            frame_data['path'] = img_info.path
            
            # Update delete button state
            if img_info.path in self.marked_for_deletion:
                frame_data['delete_btn'].config(relief=tk.RAISED, bg=DANGER, fg=WHITE)
            else:
                frame_data['delete_btn'].config(relief=tk.FLAT, bg=WHITE, fg=DANGER)
            
            # Display file path
            frame_data['path_label'].config(text=f"📁 {img_info.path}")
            
            # Display info
            size_kb = img_info.filesize / 1024
            fmt = Path(img_info.path).suffix.upper().lstrip('.') or 'IMG'
            info_text = (
                f"📏 {img_info.resolution[0]}x{img_info.resolution[1]}  •  {fmt}\n"
                f"💾 {size_kb:.1f} KB\n"
                f"📅 Modificado: {img_info.date_modified[:10]}"
            )
            if img_info.exif_date:
                info_text += f"\n📸 Tirada em: {img_info.exif_date[:10]}"
            
            frame_data['info'].config(text=info_text)
            
        except Exception as e:
            frame_data['label'].config(text=f"Erro ao carregar:\n{e}")
            frame_data['path_label'].config(text=f"📁 {img_info.path}")
    
    def _go_to_menu(self):
        self.go_back_to_menu = True
        self.root.quit()

    def _prev_group(self):
        """Show previous duplicate group."""
        if self.duplicates:
            self.current_group_idx = (self.current_group_idx - 1) % len(self.duplicates)
            self._display_group()
    
    def _next_group(self):
        """Show next duplicate group."""
        if self.duplicates:
            self.current_group_idx = (self.current_group_idx + 1) % len(self.duplicates)
            self._display_group()
    
    def _toggle_delete(self, frame_idx: int):
        """Toggle delete mark for image at frame index."""
        frame_data = self.image_frames[frame_idx]
        if not frame_data['path']:
            return
        
        path = frame_data['path']
        
        # Toggle
        if path in self.marked_for_deletion:
            self.marked_for_deletion.remove(path)
            logger.info("Unmarked for deletion: %s", path)
            frame_data['delete_btn'].config(relief=tk.FLAT, bg=WHITE, fg=DANGER)
        else:
            self.marked_for_deletion.add(path)
            logger.info("Marked for deletion: %s", path)
            frame_data['delete_btn'].config(relief=tk.RAISED, bg=DANGER, fg=WHITE)
    
    def _delete_selected(self):
        """Delete marked images."""
        if not self.marked_for_deletion:
            messagebox.showwarning("Aviso", "Nenhuma imagem marcada para eliminação!")
            return
        
        # Confirm deletion
        if not messagebox.askyesno(
            "Confirmar",
            f"Tem a certeza que quer eliminar {len(self.marked_for_deletion)} imagem(ns)?\n\nEsta ação é irreversível!"
        ):
            return
        
        logger.info("Deleting %d marked image(s)", len(self.marked_for_deletion))
        # Delete
        deleted, errors = self.scanner.delete_images(list(self.marked_for_deletion))
        
        if deleted:
            messagebox.showinfo("Sucesso", f"Eliminadas {len(deleted)} imagem(ns)")
            self.marked_for_deletion.clear()
            
            # Refresh duplicates and display
            self.duplicates = self.scanner.find_duplicates(similarity_threshold=0.85)
            self.current_group_idx = min(self.current_group_idx, max(0, len(self.duplicates) - 1))
            self._display_group()
        
        if errors:
            error_msg = "\n".join([f"{p}: {e}" for p, e in errors])
            messagebox.showerror("Erros", f"Erros ao eliminar:\n{error_msg}")

    def _show_about(self):
        win = tk.Toplevel(self.root)
        win.title("Sobre")
        win.resizable(False, False)
        win.grab_set()
        configure_premium_theme(win)

        # Center on parent
        win.update_idletasks()
        win.geometry("420x220")
        x = self.root.winfo_x() + (self.root.winfo_width() - 420) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 220) // 2
        win.geometry(f"+{x}+{y}")

        outer = ttk.Frame(win)
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(outer, text="Gestor de Fotos — Imagens Repetidas",
                  font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Versão 1.1", foreground="#94a3b8").pack(anchor="w")

        ttk.Separator(outer, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Bottom row: logo + author
        bottom = ttk.Frame(outer)
        bottom.pack(fill=tk.X)

        # Load logo
        try:
            logo_path = Path(__file__).parent / "cpnf.png"
            logo_img = Image.open(logo_path)
            logo_img.thumbnail((64, 64), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            lbl_logo = tk.Label(bottom, image=logo_photo, bg="#0f172a")
            lbl_logo.image = logo_photo  # keep reference
            lbl_logo.pack(side=tk.LEFT, padx=(0, 12))
        except Exception:
            pass

        text_col = ttk.Frame(bottom)
        text_col.pack(side=tk.LEFT, anchor="center")
        ttk.Label(text_col, text="Carlos Correia",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(text_col, text="2026 — Todos os direitos reservados",
                  foreground="#94a3b8").pack(anchor="w")

        ttk.Button(outer, text="Fechar", command=win.destroy).pack(pady=(15, 0))


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    gui = ImageDuplicateGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
