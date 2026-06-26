"""
Batch tools for photos.
Includes batch rename, batch resize, and organize by date.
"""

import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from PIL import Image, ImageTk

from exif_editor import ExifEditor
from premium_theme import BG_ALT, ACCENT, WHITE, DANGER, configure_premium_theme

SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
DATE_FORMATS = (
    '%Y:%m:%d %H:%M:%S',
    '%Y:%m:%d',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d',
    '%d/%m/%Y',
)


def collect_image_files(paths: List[str]) -> List[Path]:
    """Collect image files from the selected files and folders."""
    collected = []
    seen = set()

    for item in paths:
        path = Path(item)
        if path.is_dir():
            for file_path in path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                    resolved = str(file_path.resolve())
                    if resolved not in seen:
                        seen.add(resolved)
                        collected.append(file_path)
        elif path.is_file() and path.suffix.lower() in SUPPORTED_FORMATS:
            resolved = str(path.resolve())
            if resolved not in seen:
                seen.add(resolved)
                collected.append(path)

    return sorted(collected)


def parse_photo_datetime(file_path: Path) -> datetime:
    """Get best date for a file from EXIF or filesystem."""
    try:
        exif_editor = ExifEditor(str(file_path))
        date_value = exif_editor.get_date_taken()
        if date_value:
            for date_format in DATE_FORMATS:
                try:
                    return datetime.strptime(date_value, date_format)
                except ValueError:
                    continue
    except Exception:
        pass

    return datetime.fromtimestamp(file_path.stat().st_mtime)


def parse_input_datetime(date_input: str) -> datetime:
    """Parse user input date using the supported formats."""
    date_input = date_input.strip()
    if len(date_input) == 4 and date_input.isdigit():
        return datetime.strptime(f'{date_input}:01:01 00:00:00', '%Y:%m:%d %H:%M:%S')

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(date_input, date_format)
        except ValueError:
            continue

    raise ValueError(f'Data inválida: {date_input}')


def sanitize_filename(value: str) -> str:
    """Remove invalid filename characters."""
    value = re.sub(r'[<>:"/\\|?*]', '_', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value


def sanitize_path_pattern(value: str) -> Path:
    """Sanitize a pattern while preserving folder separators."""
    normalized = value.replace('\\', '/').strip('/ ')
    parts = []
    for part in normalized.split('/'):
        clean_part = sanitize_filename(part)
        if clean_part:
            parts.append(clean_part)
    return Path(*parts)


def ensure_unique_path(path: Path) -> Path:
    """Generate a unique path if the file already exists."""
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.with_name(f'{path.stem}_{counter}{path.suffix}')
        if not candidate.exists():
            return candidate
        counter += 1


class BaseBatchWindow:
    """Common UI and file handling for batch tools."""

    window_title = 'Ferramenta em lote'

    def __init__(self, root: tk.Tk):
        self.root = root
        configure_premium_theme(self.root)
        self.root.title(self.window_title)
        self.root.geometry('1200x780')

        self.source_root: Optional[Path] = None
        self.files: List[Path] = []
        self.current_idx = 0
        self.preview_image = None
        self.go_back_to_menu = False

        self._build_ui()

    def _build_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(top_frame, text='📁 Selecionar Pasta', command=self._select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='➕ Adicionar Ficheiros', command=self._add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='🏠 Menu', command=self._go_to_menu).pack(side=tk.RIGHT, padx=5)

        self.status_label = ttk.Label(top_frame, text='Nenhum ficheiro selecionado')
        self.status_label.pack(side=tk.LEFT, padx=20)

        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=1)

        ttk.Label(left_frame, text='Ficheiros').pack(anchor=tk.W)
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self._on_list_select)

        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=list_scroll.set)

        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=2)

        preview_box = ttk.LabelFrame(right_frame, text='Pré-visualização')
        preview_box.pack(fill=tk.BOTH, expand=True)

        self.preview_label = tk.Label(preview_box, bg='gray20', text='Nenhuma imagem')
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.detail_label = ttk.Label(right_frame, text='', justify=tk.LEFT, wraplength=650)
        self.detail_label.pack(fill=tk.X, pady=8)

        self._build_action_ui()

    def _go_to_menu(self):
        self.go_back_to_menu = True
        self.root.quit()

    def _build_action_ui(self):
        """Hook for subclasses."""
        raise NotImplementedError

    def _select_folder(self):
        folder = filedialog.askdirectory(title='Selecione a pasta com fotos')
        if not folder:
            return
        self.source_root = Path(folder)
        self._load_paths([folder])

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title='Selecione ficheiros',
            filetypes=[('Imagens', '*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff')]
        )
        if not files:
            return
        self._load_paths(list(files))

    def _load_paths(self, paths: List[str]):
        self.files = collect_image_files(paths)
        if self.files and self.source_root is None:
            try:
                common_root = os.path.commonpath([str(path.parent) for path in self.files])
                self.source_root = Path(common_root)
            except Exception:
                self.source_root = self.files[0].parent
        self.current_idx = 0
        self._refresh_file_list()

        if self.files:
            self.status_label.config(text=f'{len(self.files)} ficheiro(s) carregado(s)')
            self._display_current_file()
        else:
            self.status_label.config(text='Nenhum ficheiro compatível encontrado')
            self._clear_preview()

        self._refresh_action_preview()

    def _refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for file_path in self.files:
            self.file_listbox.insert(tk.END, file_path.name)
        if self.files:
            self.file_listbox.selection_set(0)
            self.file_listbox.activate(0)

    def _on_list_select(self, _event=None):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        self.current_idx = selection[0]
        self._display_current_file()
        self._refresh_action_preview()

    def _display_current_file(self):
        if not self.files:
            self._clear_preview()
            return

        file_path = self.files[self.current_idx]
        self.detail_label.config(
            text=(
                f'Ficheiro: {file_path.name}\n'
                f'Caminho: {file_path}\n'
                f'Tamanho: {file_path.stat().st_size / 1024:.1f} KB\n'
                f'Data: {parse_photo_datetime(file_path).strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )

        try:
            with Image.open(file_path) as image:
                image.thumbnail((620, 420), Image.Resampling.LANCZOS)
                preview = ImageTk.PhotoImage(image)
                self.preview_label.config(image=preview, text='')
                self.preview_label.image = preview
                self.preview_image = preview
        except Exception as e:
            self.preview_label.config(image='', text=f'Erro ao abrir imagem:\n{e}')
            self.preview_label.image = None
            self.preview_image = None

    def _clear_preview(self):
        self.preview_label.config(image='', text='Nenhuma imagem')
        self.preview_label.image = None
        self.preview_image = None
        self.detail_label.config(text='')

    def _refresh_action_preview(self):
        """Hook for subclasses."""
        pass

    def _next_file(self):
        if self.files:
            self.current_idx = (self.current_idx + 1) % len(self.files)
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.current_idx)
            self.file_listbox.see(self.current_idx)
            self._display_current_file()
            self._refresh_action_preview()

    def _prev_file(self):
        if self.files:
            self.current_idx = (self.current_idx - 1) % len(self.files)
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.current_idx)
            self.file_listbox.see(self.current_idx)
            self._display_current_file()
            self._refresh_action_preview()


class BatchRenameGUI(BaseBatchWindow):
    window_title = 'Renomear Ficheiros em Lote'

    def _build_action_ui(self):
        action_box = ttk.LabelFrame(self.root, text='Renomeação')
        action_box.pack(fill=tk.X, padx=10, pady=10)

        pattern_row = ttk.Frame(action_box)
        pattern_row.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(pattern_row, text='Presets:').pack(side=tk.LEFT)
        self.pattern_combo = ttk.Combobox(
            pattern_row,
            values=[
                '{year}-{month}-{day}_{counter:03d}',
                '{date}_{orig}',
                '{year}/{month}/{day}_{counter:03d}',
                '{year}_{counter:03d}_{orig}',
                '{date}_{counter:03d}',
            ],
            state='readonly'
        )
        self.pattern_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self.pattern_combo.current(0)

        ttk.Button(pattern_row, text='Usar preset', command=self._apply_pattern_preset).pack(side=tk.LEFT, padx=5)

        custom_row = ttk.Frame(action_box)
        custom_row.pack(fill=tk.X, padx=10, pady=4)
        ttk.Label(custom_row, text='Padrão personalizado:').pack(side=tk.LEFT)
        self.pattern_entry = ttk.Entry(custom_row)
        self.pattern_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self.pattern_entry.insert(0, '{year}-{month}-{day}_{counter:03d}')

        options_row = ttk.Frame(action_box)
        options_row.pack(fill=tk.X, padx=10, pady=4)
        ttk.Label(options_row, text='Contador inicial:').pack(side=tk.LEFT)
        self.counter_start_entry = ttk.Entry(options_row, width=8)
        self.counter_start_entry.pack(side=tk.LEFT, padx=5)
        self.counter_start_entry.insert(0, '1')

        self.keep_ext_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row, text='Manter extensão original', variable=self.keep_ext_var).pack(side=tk.LEFT, padx=15)

        ttk.Button(options_row, text='Atualizar pré-visualização', command=self._refresh_action_preview).pack(side=tk.RIGHT, padx=5)
        ttk.Button(options_row, text='Renomear ficheiros', command=self._rename_files).pack(side=tk.RIGHT, padx=5)

        help_text = (
            'Campos: {year}, {month}, {day}, {hour}, {minute}, {second}, {date}, {time}, {counter}, {orig}, {name}. '
            'Exemplo: {year}-{month}-{day}_{counter:03d}'
        )
        ttk.Label(action_box, text=help_text, wraplength=1100).pack(fill=tk.X, padx=10, pady=(0, 8))

        tree_frame = ttk.Frame(action_box)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.rename_tree = ttk.Treeview(tree_frame, columns=('atual', 'novo', 'destino'), show='headings', height=8)
        self.rename_tree.heading('atual', text='Nome atual')
        self.rename_tree.heading('novo', text='Novo nome')
        self.rename_tree.heading('destino', text='Caminho destino')
        self.rename_tree.column('atual', width=300)
        self.rename_tree.column('novo', width=280)
        self.rename_tree.column('destino', width=360)
        self.rename_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.rename_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.rename_tree.config(yscrollcommand=tree_scroll.set)

        self.action_status = ttk.Label(self.root, text='', foreground='green')
        self.action_status.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _apply_pattern_preset(self):
        pattern = self.pattern_combo.get().strip()
        if pattern:
            self.pattern_entry.delete(0, tk.END)
            self.pattern_entry.insert(0, pattern)
            self._refresh_action_preview()

    def _build_name(self, file_path: Path, counter: int) -> str:
        dt = parse_photo_datetime(file_path)
        pattern = self.pattern_entry.get().strip() or '{year}-{month}-{day}_{counter:03d}'
        counter_start = 1
        try:
            counter_start = int(self.counter_start_entry.get().strip() or '1')
        except ValueError:
            counter_start = 1
        values = {
            'year': dt.strftime('%Y'),
            'month': dt.strftime('%m'),
            'day': dt.strftime('%d'),
            'hour': dt.strftime('%H'),
            'minute': dt.strftime('%M'),
            'second': dt.strftime('%S'),
            'date': dt.strftime('%Y-%m-%d'),
            'time': dt.strftime('%H-%M-%S'),
            'counter': counter_start + counter - 1,
            'orig': sanitize_filename(file_path.stem),
            'name': sanitize_filename(file_path.stem),
        }
        new_base = pattern.format(**values)
        extension = file_path.suffix if self.keep_ext_var.get() else file_path.suffix.lower()
        if not extension:
            extension = file_path.suffix
        path_part = sanitize_path_pattern(new_base)
        if len(path_part.parts) == 1:
            return f'{path_part.name}{extension}'
        return str(path_part.with_suffix(extension))

    def _refresh_action_preview(self):
        for item in self.rename_tree.get_children():
            self.rename_tree.delete(item)

        if not self.files:
            return

        for index, file_path in enumerate(self.files, start=1):
            new_name = self._build_name(file_path, index)
            target_path = file_path.parent / Path(new_name)
            self.rename_tree.insert('', tk.END, values=(str(file_path), new_name, str(target_path)))

    def _rename_files(self):
        if not self.files:
            messagebox.showwarning('Aviso', 'Selecione ficheiros primeiro.')
            return

        if not messagebox.askyesno('Confirmar', f'Renomear {len(self.files)} ficheiro(s)?'):
            return

        logger.info('Batch rename started for %d file(s)', len(self.files))
        renamed = []
        errors = []
        updated_files = []

        for index, file_path in enumerate(self.files, start=1):
            try:
                new_name = self._build_name(file_path, index)
                target = ensure_unique_path(file_path.parent / Path(new_name))
                target.parent.mkdir(parents=True, exist_ok=True)
                file_path.rename(target)
                renamed.append(target)
                updated_files.append(target)
            except Exception as e:
                errors.append(f'{file_path}: {e}')

        if renamed:
            self.files = updated_files
        self.source_root = self.source_root or (self.files[0].parent if self.files else None)
        self._refresh_file_list()
        self._refresh_action_preview()
        self._display_current_file()

        if renamed:
            self.action_status.config(text=f'Renomeados {len(renamed)} ficheiro(s)')
        if errors:
            messagebox.showerror('Erros', '\n'.join(errors))


class BatchResizeGUI(BaseBatchWindow):
    window_title = 'Redimensionar Ficheiros em Lote'

    def _build_action_ui(self):
        action_box = ttk.LabelFrame(self.root, text='Redimensionamento')
        action_box.pack(fill=tk.X, padx=10, pady=10)

        row1 = ttk.Frame(action_box)
        row1.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(row1, text='Presets:').pack(side=tk.LEFT)
        self.resize_preset_combo = ttk.Combobox(
            row1,
            values=['Web 1920', 'Web 1600', 'Facebook 1200', 'Instagram 1080', 'Mobile 800', 'Custom'],
            state='readonly',
            width=16
        )
        self.resize_preset_combo.pack(side=tk.LEFT, padx=5)
        self.resize_preset_combo.current(0)
        self.resize_preset_combo.bind('<<ComboboxSelected>>', self._apply_resize_preset)

        ttk.Label(row1, text='Tamanho máximo (px):').pack(side=tk.LEFT, padx=(15, 0))
        self.max_size_entry = ttk.Entry(row1, width=10)
        self.max_size_entry.pack(side=tk.LEFT, padx=5)
        self.max_size_entry.insert(0, '1920')

        ttk.Label(row1, text='Qualidade JPEG:').pack(side=tk.LEFT, padx=(20, 0))
        self.quality_scale = tk.Scale(row1, from_=50, to=95, orient=tk.HORIZONTAL, length=180)
        self.quality_scale.set(85)
        self.quality_scale.pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(action_box)
        row2.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(row2, text='Pasta de saída:').pack(side=tk.LEFT)
        self.output_entry = ttk.Entry(row2)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(row2, text='Escolher', command=self._choose_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text='Redimensionar', command=self._resize_files).pack(side=tk.LEFT, padx=5)

        self.keep_structure_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(action_box, text='Manter estrutura de pastas', variable=self.keep_structure_var).pack(anchor=tk.W, padx=10, pady=(0, 8))

        self.mode_var = tk.StringVar(value='copy')
        mode_row = ttk.Frame(action_box)
        mode_row.pack(fill=tk.X, padx=10, pady=(0, 8))
        ttk.Label(mode_row, text='Modo:').pack(side=tk.LEFT)
        ttk.Radiobutton(mode_row, text='Criar cópias', value='copy', variable=self.mode_var).pack(side=tk.LEFT, padx=8)
        ttk.Radiobutton(mode_row, text='Substituir originais', value='replace', variable=self.mode_var).pack(side=tk.LEFT, padx=8)

        self.action_status = ttk.Label(self.root, text='', foreground='green')
        self.action_status.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _apply_resize_preset(self, _event=None):
        preset = self.resize_preset_combo.get()
        sizes = {
            'Web 1920': 1920,
            'Web 1600': 1600,
            'Facebook 1200': 1200,
            'Instagram 1080': 1080,
            'Mobile 800': 800,
        }
        if preset in sizes:
            self.max_size_entry.delete(0, tk.END)
            self.max_size_entry.insert(0, str(sizes[preset]))

    def _choose_output_folder(self):
        folder = filedialog.askdirectory(title='Escolha a pasta de saída')
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)

    def _refresh_action_preview(self):
        pass

    def _resize_files(self):
        if not self.files:
            messagebox.showwarning('Aviso', 'Selecione ficheiros primeiro.')
            return

        try:
            max_size = int(self.max_size_entry.get().strip())
        except ValueError:
            messagebox.showerror('Erro', 'Tamanho máximo inválido.')
            return

        output_root_text = self.output_entry.get().strip()
        if output_root_text:
            output_root = Path(output_root_text)
        elif self.source_root:
            output_root = self.source_root / 'redimensionadas'
        else:
            output_root = self.files[0].parent / 'redimensionadas'

        output_root.mkdir(parents=True, exist_ok=True)
        quality = int(self.quality_scale.get())
        keep_structure = self.keep_structure_var.get()

        if not messagebox.askyesno('Confirmar', f'Guardar cópias redimensionadas em:\n{output_root}\n\nProcessar {len(self.files)} ficheiro(s)?'):
            return

        logger.info('Batch resize started for %d file(s) into %s', len(self.files), output_root)
        resized = []
        errors = []
        replace_mode = self.mode_var.get() == 'replace'

        for file_path in self.files:
            try:
                if replace_mode:
                    destination_dir = file_path.parent
                elif keep_structure and self.source_root and self.source_root in file_path.parents:
                    relative_parent = file_path.parent.relative_to(self.source_root)
                    destination_dir = output_root / relative_parent
                else:
                    destination_dir = output_root
                destination_dir.mkdir(parents=True, exist_ok=True)

                with Image.open(file_path) as image:
                    image = image.copy()
                    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    save_kwargs = {'optimize': True}
                    if file_path.suffix.lower() in {'.jpg', '.jpeg'}:
                        save_kwargs['quality'] = quality
                        save_kwargs['progressive'] = True
                    if replace_mode:
                        temp_destination = file_path.with_name(f'{file_path.stem}.__tmp__{file_path.suffix}')
                        image.save(temp_destination, **save_kwargs)
                        os.replace(temp_destination, file_path)
                        destination = file_path
                    else:
                        destination = destination_dir / file_path.name
                        if destination.exists():
                            destination = ensure_unique_path(destination)
                        image.save(destination, **save_kwargs)

                resized.append(destination)
            except Exception as e:
                errors.append(f'{file_path}: {e}')

        self.action_status.config(text=f'Processados {len(resized)} ficheiro(s)')
        if errors:
            messagebox.showerror('Erros', '\n'.join(errors))
        else:
            messagebox.showinfo('Sucesso', f'Concluído: {len(resized)} ficheiro(s).')


class OrganizeByDateGUI(BaseBatchWindow):
    window_title = 'Organizar Ficheiros por Data'

    def _build_action_ui(self):
        action_box = ttk.LabelFrame(self.root, text='Organização por data')
        action_box.pack(fill=tk.X, padx=10, pady=10)

        row1 = ttk.Frame(action_box)
        row1.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(row1, text='Pasta raiz de destino:').pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(row1)
        self.target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(row1, text='Escolher', command=self._choose_target_folder).pack(side=tk.LEFT, padx=5)

        row2 = ttk.Frame(action_box)
        row2.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(row2, text='Estrutura:').pack(side=tk.LEFT)
        self.structure_combo = ttk.Combobox(row2, values=['Ano', 'Ano/Mês', 'Ano/Mês/Dia'], state='readonly', width=15)
        self.structure_combo.current(2)
        self.structure_combo.pack(side=tk.LEFT, padx=5)

        self.move_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2, text='Mover ficheiros (desmarcar para copiar)', variable=self.move_var).pack(side=tk.LEFT, padx=20)

        ttk.Button(row2, text='Organizar por Data', command=self._organize_files).pack(side=tk.RIGHT, padx=5)

        self.action_status = ttk.Label(self.root, text='', foreground='green')
        self.action_status.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _choose_target_folder(self):
        folder = filedialog.askdirectory(title='Escolha a pasta raiz de destino')
        if folder:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, folder)

    def _refresh_action_preview(self):
        pass

    def _organize_files(self):
        if not self.files:
            messagebox.showwarning('Aviso', 'Selecione ficheiros primeiro.')
            return

        target_root_text = self.target_entry.get().strip()
        if target_root_text:
            target_root = Path(target_root_text)
        elif self.source_root:
            target_root = self.source_root
        else:
            target_root = self.files[0].parent

        target_root.mkdir(parents=True, exist_ok=True)
        structure = self.structure_combo.get()
        move_files = self.move_var.get()

        if not messagebox.askyesno('Confirmar', f'Organizar {len(self.files)} ficheiro(s) em:\n{target_root}\n\nModo: {"Mover" if move_files else "Copiar"}'): 
            return

        logger.info('Organize-by-date started for %d file(s) into %s', len(self.files), target_root)
        processed = []
        errors = []

        for file_path in self.files:
            try:
                dt = parse_photo_datetime(file_path)
                parts = [dt.strftime('%Y')]
                if structure in ('Ano/Mês', 'Ano/Mês/Dia'):
                    parts.append(dt.strftime('%m'))
                if structure == 'Ano/Mês/Dia':
                    parts.append(dt.strftime('%d'))

                destination_dir = target_root.joinpath(*parts)
                destination_dir.mkdir(parents=True, exist_ok=True)
                destination = ensure_unique_path(destination_dir / file_path.name)

                if move_files:
                    shutil.move(str(file_path), str(destination))
                else:
                    shutil.copy2(str(file_path), str(destination))
                processed.append(destination)
            except Exception as e:
                errors.append(f'{file_path}: {e}')

        self.action_status.config(text=f'Processados {len(processed)} ficheiro(s)')
        if errors:
            messagebox.showerror('Erros', '\n'.join(errors))
        else:
            messagebox.showinfo('Sucesso', f'Concluído: {len(processed)} ficheiro(s).')

        if move_files:
            if self.source_root and self.source_root.exists():
                self._load_paths([str(self.source_root)])
            else:
                self.files = []
                self._refresh_file_list()
                self._clear_preview()


class BatchToolsMenu:
    """Menu for batch tools in the requested order."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Ferramentas em Lote')
        self.root.geometry('560x420')
        self.selected = None
        self._create_ui()

    def _create_ui(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(frame, text='Ferramentas em Lote', font=('Arial', 18, 'bold')).pack(pady=(0, 10))
        ttk.Label(frame, text='Escolha a operação pretendida, por ordem de implementação.', wraplength=460).pack(pady=(0, 20))

        options = [
            ('1. Renomear em lote', 'rename_batch', 'Renomear ficheiros com presets, contador e caminho destino.'),
            ('2. Redimensionar em lote', 'resize_batch', 'Criar cópias redimensionadas ou substituir originais.'),
            ('3. Organizar por data', 'organize_by_date', 'Mover ou copiar para pastas Ano, Ano/Mês ou Ano/Mês/Dia.'),
        ]

        for label, value, description in options:
            box = ttk.LabelFrame(frame, text='', padding=12)
            box.pack(fill=tk.X, pady=8)
            ttk.Label(box, text=label, font=('Arial', 12, 'bold')).pack(anchor=tk.W)
            ttk.Label(box, text=description, wraplength=420).pack(anchor=tk.W, pady=(4, 8))
            ttk.Button(box, text='Abrir', command=lambda choice=value: self._select(choice)).pack(anchor=tk.E)

        ttk.Button(frame, text='🏠 Voltar ao Menu Principal',
                   command=self._go_back).pack(pady=(10, 0))

    def _select(self, value: str):
        self.selected = value
        self.root.quit()

    def _go_back(self):
        self.selected = None
        self.root.quit()


def show_batch_tools_menu(root: "tk.Tk" = None):
    if root is None:
        root = tk.Tk()
    for widget in root.winfo_children():
        widget.destroy()
    root.resizable(True, True)
    root.deiconify()
    menu = BatchToolsMenu(root)
    root.protocol("WM_DELETE_WINDOW", root.quit)  # X button = quit mainloop, not destroy
    root.mainloop()
    root.protocol("WM_DELETE_WINDOW", "")  # reset
    return menu.selected


if __name__ == '__main__':
    choice = show_batch_tools_menu()
    print(choice)
