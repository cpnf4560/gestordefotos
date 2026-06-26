#!/usr/bin/env python3
"""
Main entry point for Verificador de Imagens Repetidas.

Usage:
    python main.py                  # Launch menu
    python main.py duplicates       # Launch duplicate finder directly
    python main.py exif             # Launch EXIF editor directly
    python main.py batch_tools      # Launch batch tools menu directly
"""

import sys
import logging
from pathlib import Path

def setup_logging():
    """Configure console and file logging for the app."""
    project_root = Path(__file__).resolve().parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    handlers = [
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True,
    )

    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.getLogger("verificador").error(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_uncaught_exception
    logging.captureWarnings(True)
    return logging.getLogger("verificador")


logger = setup_logging()

try:
    import tkinter as tk
    from gui import ImageDuplicateGUI
    from exif_editor import ExifEditorGUI
    from batch_tools import BatchRenameGUI, BatchResizeGUI, OrganizeByDateGUI, show_batch_tools_menu
    from menu_screen import show_menu
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("\nInstale as dependências com:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def _clear_root(root: "tk.Tk"):
    """Destroy all child widgets and reset root constraints."""
    for widget in root.winfo_children():
        widget.destroy()
    root.resizable(True, True)


def launch_tool(mode: str, root: "tk.Tk") -> bool:
    """Launch tool for given mode on existing root. Returns True if user wants to go back to menu."""
    _clear_root(root)

    def tk_error_handler(exc, val, tb):
        import traceback
        logger.error("Tkinter error: %s\n%s", val, "".join(traceback.format_tb(tb)))
    root.report_callback_exception = tk_error_handler

    if mode == "duplicates":
        print("🔍 Abrindo Procurador de Imagens Repetidas...")
        gui = ImageDuplicateGUI(root)
        logger.info("Opened duplicate finder")
    elif mode == "exif_editor":
        print("📅 Abrindo Editor de Data de Fotos...")
        gui = ExifEditorGUI(root)
        logger.info("Opened EXIF editor")
    elif mode == "rename_batch":
        print("✏️ Abrindo Renomeação em Lote...")
        gui = BatchRenameGUI(root)
        logger.info("Opened batch rename tool")
    elif mode == "resize_batch":
        print("🖼️ Abrindo Redimensionamento em Lote...")
        gui = BatchResizeGUI(root)
        logger.info("Opened batch resize tool")
    elif mode == "organize_by_date":
        print("📂 Abrindo Organização por Data...")
        gui = OrganizeByDateGUI(root)
        logger.info("Opened organize-by-date tool")
    else:
        print(f"❌ Modo desconhecido: {mode}")
        return False

    root.protocol("WM_DELETE_WINDOW", root.quit)  # X button = quit mainloop, not destroy
    root.mainloop()
    root.protocol("WM_DELETE_WINDOW", "")  # reset
    return getattr(gui, 'go_back_to_menu', False)


def main():
    """Main entry point."""
    logger.info("Starting application")
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║          Gestor de Fotos v1.1                          ║
    ║     Duplicados  •  EXIF  •  Ferramentas em lote         ║
    ╚════════════════════════════════════════════════════════╝
    """)

    root = tk.Tk()
    root.withdraw()  # hide until first screen is ready

    def tk_error_handler(exc, val, tb):
        import traceback
        logger.error("Tkinter error: %s\n%s", val, "".join(traceback.format_tb(tb)))
    root.report_callback_exception = tk_error_handler

    # If mode passed as argument, launch directly (no menu loop)
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        logger.info("Requested mode: %s", mode)
        if mode == "batch_tools":
            mode = show_batch_tools_menu(root)
        if mode:
            launch_tool(mode, root)
        root.destroy()
        return

    # Menu loop — single root, reused for every screen
    while True:
        mode = show_menu(root)
        if not mode:
            break

        if mode == "batch_tools":
            mode = show_batch_tools_menu(root)
        if not mode:
            continue

        logger.info("Resolved mode: %s", mode)
        go_back = launch_tool(mode, root)
        if not go_back:
            break

    try:
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    main()
