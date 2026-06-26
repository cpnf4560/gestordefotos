"""
EXIF date editor for photos.
Modify photo metadata, especially date taken.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from PIL.ExifTags import TAGS
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import threading
import logging

from premium_theme import BG_ALT, BG_PANEL, CARD, ACCENT_2, configure_premium_theme

logger = logging.getLogger(__name__)


class ExifEditor:
    """Edit EXIF metadata in photos."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.original_exif = None
        self.load_exif()
    
    def load_exif(self):
        """Load EXIF data from image."""
        try:
            with Image.open(self.file_path) as img:
                exif = img._getexif()
                if exif:
                    self.original_exif = {
                        TAGS.get(k, k): v 
                        for k, v in exif.items()
                    }
        except Exception as e:
            logger.error(f"Failed to load EXIF: {e}")
            self.original_exif = {}
    
    def get_date_taken(self) -> Optional[str]:
        """Get date taken from EXIF or file modification date."""
        if not self.original_exif:
            return None
        
        for key in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
            if key in self.original_exif:
                return str(self.original_exif[key])
        
        return None
    
    def get_file_modification_date(self) -> str:
        """Get file modification date."""
        timestamp = self.file_path.stat().st_mtime
        return datetime.fromtimestamp(timestamp).strftime('%Y:%m:%d %H:%M:%S')
    
    def set_date_taken(self, date_str: str) -> bool:
        """
        Set date taken in EXIF.
        Format: 'YYYY:MM:DD HH:MM:SS' or 'YYYY:MM:DD' or 'YYYY'
        """
        try:
            # Normalize date string
            date_str = self._normalize_date(date_str)
            
            # For now, just update file modification date
            # Full EXIF rewriting requires more complex logic
            self._update_file_date(date_str)
            
            return True
        except Exception as e:
            logger.error(f"Failed to set date: {e}")
            return False
    
    def _normalize_date(self, date_input: str) -> Tuple[str, float]:
        """
        Normalize various date formats to EXIF format and Unix timestamp.
        
        Accepts:
        - 'YYYY'
        - 'YYYY:MM:DD'
        - 'YYYY:MM:DD HH:MM:SS'
        - 'YYYY-MM-DD'
        - 'DD/MM/YYYY'
        """
        date_input = date_input.strip()
        
        # Try year only
        if len(date_input) == 4 and date_input.isdigit():
            date_str = f"{date_input}:01:01 00:00:00"
            dt = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        
        # Try YYYY:MM:DD format
        elif ':' in date_input and len(date_input.split(':')) == 3 and ' ' not in date_input:
            dt = datetime.strptime(date_input, '%Y:%m:%d')
            date_str = dt.strftime('%Y:%m:%d 00:00:00')
        
        # Try YYYY:MM:DD HH:MM:SS format
        elif ':' in date_input and len(date_input.split(' ')) == 2:
            dt = datetime.strptime(date_input, '%Y:%m:%d %H:%M:%S')
            date_str = date_input
        
        # Try YYYY-MM-DD format
        elif '-' in date_input and len(date_input) == 10:
            dt = datetime.strptime(date_input, '%Y-%m-%d')
            date_str = dt.strftime('%Y:%m:%d 00:00:00')
        
        # Try DD/MM/YYYY format
        elif '/' in date_input:
            dt = datetime.strptime(date_input, '%d/%m/%Y')
            date_str = dt.strftime('%Y:%m:%d 00:00:00')
        
        else:
            raise ValueError(f"Unrecognized date format: {date_input}")
        
        timestamp = dt.timestamp()
        return date_str, timestamp
    
    def _update_file_date(self, date_str: str):
        """Update file modification date."""
        _, timestamp = self._normalize_date(date_str)
        os.utime(self.file_path, (timestamp, timestamp))


class ExifEditorGUI:
    """GUI for batch editing photo dates."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        configure_premium_theme(self.root)
        self.root.title("Editor de Data de Fotos")
        self.root.geometry("1000x700")
        
        self.files: List[str] = []
        self.current_idx = 0
        self.editors: Dict[str, ExifEditor] = {}
        self.go_back_to_menu = False
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components."""
        # Top frame: controls
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(top_frame, text="📁 Selecionar Pasta com Fotos",
                  command=self._select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="➕ Adicionar Ficheiros",
                  command=self._add_files).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(top_frame, text="Nenhum ficheiro selecionado")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Info frame
        info_frame = ttk.LabelFrame(self.root, text="Informação da Foto")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.info_label = ttk.Label(info_frame, text="", justify=tk.LEFT)
        self.info_label.pack(fill=tk.X, padx=10, pady=10)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(self.root, text="Pré-visualização")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.preview_label = tk.Label(preview_frame, bg=BG_ALT, text="Nenhuma imagem")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Edit frame
        edit_frame = ttk.LabelFrame(self.root, text="Modificar Data")
        edit_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(edit_frame, text="Nova data:").pack(side=tk.LEFT, padx=5, pady=5)
        self.date_entry = ttk.Entry(edit_frame, width=30)
        self.date_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(edit_frame, text="Formatos: YYYY (só ano) | YYYY:MM:DD | YYYY:MM:DD HH:MM:SS | DD/MM/YYYY").pack(side=tk.LEFT, padx=5, pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="⬅ Anterior",
                  command=self._prev_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Próximo ➡",
                  command=self._next_file).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="✓ Guardar Data",
                  command=self._save_date).pack(side=tk.LEFT, padx=20)
        ttk.Button(buttons_frame, text="✓ Guardar Tudo",
                  command=self._save_all).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="🔄 Atualizar",
                  command=self._refresh_display).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🏠 Menu",
                  command=self._go_to_menu).pack(side=tk.LEFT, padx=20)
        
        self.save_label = ttk.Label(buttons_frame, text="", foreground="green")
        self.save_label.pack(side=tk.RIGHT, padx=5)
    
    def _go_to_menu(self):
        self.go_back_to_menu = True
        self.root.quit()

    def _select_folder(self):
        """Select folder with photos."""
        folder = filedialog.askdirectory(title="Selecione pasta com fotos")
        if folder:
            self._load_folder(folder)
    
    def _load_folder(self, folder: str):
        """Load all photos from folder."""
        logger.info("Loading EXIF editor folder: %s", folder)
        self.files = []
        self.editors = {}
        
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp']:
            self.files.extend(Path(folder).rglob(ext))
            self.files.extend(Path(folder).rglob(ext.upper()))
        
        self.files = sorted(list(set(self.files)))  # Remove duplicates
        
        if self.files:
            self.status_label.config(text=f"Carregadas {len(self.files)} fotos")
            for f in self.files:
                self.editors[str(f)] = ExifEditor(str(f))
            self.current_idx = 0
            self._display_file()
        else:
            messagebox.showwarning("Aviso", "Nenhuma foto encontrada nesta pasta")
    
    def _add_files(self):
        """Add individual photo files."""
        files = filedialog.askopenfilenames(
            title="Selecione fotos",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")]
        )
        if files:
            for f in files:
                if f not in self.editors:
                    self.files.append(f)
                    self.editors[f] = ExifEditor(f)
            self.files.sort()
            self.status_label.config(text=f"Total: {len(self.files)} fotos")
            self.current_idx = 0
            self._display_file()
    
    def _display_file(self):
        """Display current file info and preview."""
        if not self.files:
            self.info_label.config(text="Nenhum ficheiro carregado")
            self.preview_label.config(image='', text="Nenhuma imagem")
            return
        
        file_path = self.files[self.current_idx]
        editor = self.editors[file_path]
        
        # Update info
        current_date = editor.get_date_taken() or editor.get_file_modification_date()
        info_text = (
            f"Ficheiro: {file_path}\n"
            f"Pasta: {Path(file_path).parent}\n"
            f"Data atual: {current_date}\n"
            f"Foto {self.current_idx + 1} de {len(self.files)}"
        )
        self.info_label.config(text=info_text)
        
        # Load preview
        try:
            img = Image.open(file_path)
            img.thumbnail((800, 500), Image.Resampling.LANCZOS)
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(img)
            
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo
        except Exception as e:
            self.preview_label.config(text=f"Erro ao carregar:\n{e}")
        
        # Clear date entry
        self.date_entry.delete(0, tk.END)
        self.save_label.config(text="")
    
    def _prev_file(self):
        """Go to previous file."""
        if self.files:
            self.current_idx = (self.current_idx - 1) % len(self.files)
            self._display_file()
    
    def _next_file(self):
        """Go to next file."""
        if self.files:
            self.current_idx = (self.current_idx + 1) % len(self.files)
            self._display_file()
    
    def _save_date(self):
        """Save date for current file."""
        if not self.files:
            messagebox.showwarning("Aviso", "Nenhum ficheiro selecionado")
            return
        
        date_input = self.date_entry.get().strip()
        if not date_input:
            messagebox.showwarning("Aviso", "Introduza uma data")
            return
        
        file_path = self.files[self.current_idx]
        editor = self.editors[file_path]
        
        try:
            logger.info("Saving date for file: %s -> %s", file_path, date_input)
            if editor.set_date_taken(date_input):
                self.save_label.config(text="✓ Guardado!", foreground="green")
                self._display_file()
                self.root.after(2000, lambda: self.save_label.config(text=""))
            else:
                messagebox.showerror("Erro", "Não foi possível guardar a data")
        except ValueError as e:
            messagebox.showerror("Erro", f"Data inválida: {e}")
    
    def _save_all(self):
        """Save dates for all files (requires same date)."""
        date_input = self.date_entry.get().strip()
        if not date_input:
            messagebox.showwarning("Aviso", "Introduza uma data")
            return
        
        if not messagebox.askyesno("Confirmar", f"Atualizar {len(self.files)} fotos com esta data?"):
            return
        
        success = 0
        errors = []
        logger.info("Saving date for all files: %s", date_input)
        
        for file_path in self.files:
            editor = self.editors[file_path]
            try:
                if editor.set_date_taken(date_input):
                    success += 1
                else:
                    errors.append(file_path)
            except Exception as e:
                errors.append(f"{file_path}: {e}")
        
        result_msg = f"Atualizadas {success}/{len(self.files)} fotos"
        if errors:
            result_msg += f"\n\nErros: {len(errors)}"
        
        messagebox.showinfo("Resultado", result_msg)
        self._display_file()
    
    def _refresh_display(self):
        """Refresh display."""
        self._display_file()


def launch_exif_editor():
    """Launch EXIF editor window."""
    root = tk.Tk()
    gui = ExifEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_exif_editor()
